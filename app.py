from flask import Flask, request, send_file, jsonify
import subprocess
import os
import uuid
import zipfile
import shutil

app = Flask(__name__)

# Maximum upload size: 50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024


@app.route('/')
def index():
    """Health check endpoint."""
    return jsonify({
        "service": "typst2pdf",
        "status": "running",
        "version": "1.0.0"
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check with Typst compiler verification."""
    try:
        result = subprocess.run(
            ['typst', '--version'],
            capture_output=True, text=True, timeout=10
        )
        typst_version = result.stdout.strip() if result.returncode == 0 else None
    except (subprocess.SubprocessError, FileNotFoundError):
        typst_version = None

    if typst_version:
        return jsonify({
            "status": "healthy",
            "typst_version": typst_version
        })
    else:
        return jsonify({
            "status": "unhealthy",
            "error": "Typst compiler not available"
        }), 503


@app.route('/fonts', methods=['GET'])
def list_fonts():
    """List all available fonts in the environment."""
    try:
        result = subprocess.run(
            ['typst', 'fonts'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return jsonify({"error": "Failed to list fonts"}), 500
        fonts = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        return jsonify({"fonts": fonts, "count": len(fonts)})
    except (subprocess.SubprocessError, FileNotFoundError):
        return jsonify({"error": "Typst compiler not available"}), 503


@app.route('/render', methods=['POST'])
def render_typst():
    """
    Render a Typst document to PDF.

    Accepts a ZIP file containing Typst source files and returns the compiled PDF.

    Form parameters:
        file: ZIP archive containing .typ files (required)
        entrypoint: Name of the main .typ file to compile (default: main.typ)

    Returns:
        application/pdf on success
        JSON error on failure
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded", "field": "file"}), 400

    zip_file = request.files['file']
    if zip_file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    entrypoint = request.form.get('entrypoint', 'main.typ')

    # Validate entrypoint to prevent path traversal
    if '..' in entrypoint or entrypoint.startswith('/'):
        return jsonify({"error": "Invalid entrypoint path"}), 400

    file_id = str(uuid.uuid4())
    extract_dir = f"/tmp/{file_id}"
    output_path = f"{extract_dir}/output.pdf"

    os.makedirs(extract_dir, exist_ok=True)

    try:
        zip_path = f"{extract_dir}/upload.zip"
        zip_file.save(zip_path)

        # Extract ZIP
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except zipfile.BadZipFile:
            return jsonify({"error": "Invalid zip file"}), 400

        # Compile Typst
        input_typ = os.path.join(extract_dir, entrypoint)
        if not os.path.exists(input_typ):
            return jsonify({
                "error": f"Entrypoint not found: {entrypoint}",
                "hint": "Ensure the .typ file exists at the root of the ZIP archive"
            }), 400

        try:
            result = subprocess.run(
                ['typst', 'compile', input_typ, output_path],
                capture_output=True, text=True, timeout=60
            )
        except FileNotFoundError:
            return jsonify({"error": "Typst compiler not found on this system"}), 503
        except subprocess.TimeoutExpired:
            return jsonify({"error": "Typst compilation timed out"}), 504

        if result.returncode != 0:
            return jsonify({
                "error": "Typst compilation failed",
                "details": result.stderr.strip()
            }), 500

        if not os.path.exists(output_path):
            return jsonify({"error": "PDF output was not generated"}), 500

        return send_file(
            output_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='output.pdf'
        )
    finally:
        # Cleanup temporary files
        shutil.rmtree(extract_dir, ignore_errors=True)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
