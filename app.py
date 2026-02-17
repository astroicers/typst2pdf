from flask import Flask, request, send_file, jsonify
import typst
import os
import io
import uuid
import json
import zipfile
import shutil
import subprocess

app = Flask(__name__)

# Maximum upload size: 50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

VALID_FORMATS = {'pdf', 'png', 'svg'}
FORMAT_MIMETYPES = {
    'pdf': 'application/pdf',
    'png': 'image/png',
    'svg': 'image/svg+xml',
}


def _parse_format(value):
    """Validate and return output format."""
    fmt = (value or 'pdf').lower()
    if fmt not in VALID_FORMATS:
        return None, fmt
    return fmt, None


def _parse_ppi(value):
    """Validate and return PPI value."""
    try:
        return float(value or '144.0'), None
    except (ValueError, TypeError):
        return None, value


def _parse_sys_inputs(raw):
    """Parse and validate sys_inputs JSON string."""
    if not raw:
        return None, None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, "Invalid JSON in sys_inputs"
    if not isinstance(data, dict):
        return None, "sys_inputs must be a JSON object"
    return {str(k): str(v) for k, v in data.items()}, None


def _compile_and_respond(compile_kwargs, output_format):
    """Run typst.compile and return a Flask response."""
    try:
        result = typst.compile(**compile_kwargs)
    except Exception as e:
        return jsonify({
            "error": "Typst compilation failed",
            "details": str(e)
        }), 500

    # Multi-page PNG/SVG returns list[bytes]; take first page
    if isinstance(result, list):
        if len(result) == 0:
            return jsonify({"error": "Compilation produced no output"}), 500
        result = result[0]

    mimetype = FORMAT_MIMETYPES[output_format]
    return send_file(
        io.BytesIO(result),
        mimetype=mimetype,
        as_attachment=True,
        download_name=f'output.{output_format}'
    )


@app.route('/')
def index():
    """Service status."""
    return jsonify({
        "service": "typst2pdf",
        "status": "running",
        "version": "2.0.0",
        "compiler": "typst-py"
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check — verifies typst-py can compile."""
    try:
        typst.compile(b'ok')
        return jsonify({"status": "healthy", "compiler": "typst-py"})
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503


@app.route('/fonts', methods=['GET'])
def list_fonts():
    """List available fonts (requires Typst CLI binary)."""
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
        return jsonify({
            "error": "Font listing requires the Typst CLI binary",
            "hint": "Install the typst CLI or use the Docker image"
        }), 503


@app.route('/render', methods=['POST'])
def render_typst():
    """
    Render a Typst ZIP project to PDF/PNG/SVG.

    Form parameters:
        file:        ZIP archive containing .typ files (required)
        entrypoint:  Main .typ file in the ZIP (default: main.typ)
        format:      Output format — pdf, png, svg (default: pdf)
        ppi:         Pixels per inch for PNG output (default: 144.0)
        sys_inputs:  JSON object of key-value strings passed to Typst
    """
    # --- file validation ---
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded", "field": "file"}), 400

    zip_file = request.files['file']
    if zip_file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    entrypoint = request.form.get('entrypoint', 'main.typ')
    if '..' in entrypoint or entrypoint.startswith('/'):
        return jsonify({"error": "Invalid entrypoint path"}), 400

    # --- parameter parsing ---
    output_format, bad_fmt = _parse_format(request.form.get('format'))
    if bad_fmt:
        return jsonify({"error": f"Unsupported format: {bad_fmt}", "supported": list(VALID_FORMATS)}), 400

    ppi_value, bad_ppi = _parse_ppi(request.form.get('ppi'))
    if bad_ppi is not None:
        return jsonify({"error": f"Invalid ppi value: {bad_ppi}"}), 400

    sys_inputs, si_err = _parse_sys_inputs(request.form.get('sys_inputs'))
    if si_err:
        return jsonify({"error": si_err}), 400

    # --- extract ZIP to temp dir ---
    file_id = str(uuid.uuid4())
    extract_dir = f"/tmp/{file_id}"
    os.makedirs(extract_dir, exist_ok=True)

    try:
        zip_path = f"{extract_dir}/upload.zip"
        zip_file.save(zip_path)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        except zipfile.BadZipFile:
            return jsonify({"error": "Invalid zip file"}), 400

        input_typ = os.path.join(extract_dir, entrypoint)
        if not os.path.exists(input_typ):
            return jsonify({
                "error": f"Entrypoint not found: {entrypoint}",
                "hint": "Ensure the .typ file exists at the root of the ZIP archive"
            }), 400

        # --- compile ---
        compile_kwargs = {
            'input': input_typ,
            'root': extract_dir,
            'format': output_format,
        }
        if output_format == 'png':
            compile_kwargs['ppi'] = ppi_value
        if sys_inputs:
            compile_kwargs['sys_inputs'] = sys_inputs

        return _compile_and_respond(compile_kwargs, output_format)
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


@app.route('/render/raw', methods=['POST'])
def render_raw():
    """
    Render raw Typst source code to PDF/PNG/SVG (no ZIP needed).

    Accepts JSON body:
        {
            "source":     "Hello *World*",          // required
            "format":     "pdf",                    // optional, default: pdf
            "ppi":        144.0,                    // optional, for PNG
            "sys_inputs": {"name": "value"}         // optional
        }

    Also accepts form data:
        source:      Typst source code (required)
        format:      pdf | png | svg (default: pdf)
        ppi:         float (default: 144.0)
        sys_inputs:  JSON string
    """
    # --- parse input from JSON or form data ---
    if request.is_json:
        body = request.get_json(silent=True) or {}
        source = body.get('source')
        fmt_raw = body.get('format', 'pdf')
        ppi_raw = body.get('ppi', 144.0)
        si_raw = body.get('sys_inputs')
        # sys_inputs already a dict from JSON
        if si_raw is not None:
            if not isinstance(si_raw, dict):
                return jsonify({"error": "sys_inputs must be a JSON object"}), 400
            sys_inputs = {str(k): str(v) for k, v in si_raw.items()}
        else:
            sys_inputs = None
        si_err = None
    else:
        source = request.form.get('source')
        fmt_raw = request.form.get('format', 'pdf')
        ppi_raw = request.form.get('ppi', '144.0')
        sys_inputs, si_err = _parse_sys_inputs(request.form.get('sys_inputs'))

    if not source:
        return jsonify({"error": "No source provided", "field": "source"}), 400

    output_format, bad_fmt = _parse_format(fmt_raw)
    if bad_fmt:
        return jsonify({"error": f"Unsupported format: {bad_fmt}", "supported": list(VALID_FORMATS)}), 400

    ppi_value, bad_ppi = _parse_ppi(ppi_raw)
    if bad_ppi is not None:
        return jsonify({"error": f"Invalid ppi value: {bad_ppi}"}), 400

    if si_err:
        return jsonify({"error": si_err}), 400

    # --- compile in memory ---
    compile_kwargs = {
        'input': source.encode('utf-8') if isinstance(source, str) else source,
        'format': output_format,
    }
    if output_format == 'png':
        compile_kwargs['ppi'] = ppi_value
    if sys_inputs:
        compile_kwargs['sys_inputs'] = sys_inputs

    return _compile_and_respond(compile_kwargs, output_format)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
