from flask import Flask, request, send_file
import subprocess
import os
import uuid
import zipfile

app = Flask(__name__)

@app.route('/render', methods=['POST'])
def render_typst():
    if 'file' not in request.files:
        return "No file uploaded", 400

    zip_file = request.files['file']
    entrypoint = request.form.get('entrypoint', 'main.typ')  # 可自訂 typ 檔名

    file_id = str(uuid.uuid4())
    extract_dir = f"/tmp/{file_id}"
    output_path = f"{extract_dir}/output.pdf"

    os.makedirs(extract_dir, exist_ok=True)

    zip_path = f"{extract_dir}/upload.zip"
    zip_file.save(zip_path)

    # 解壓縮
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    except zipfile.BadZipFile:
        return "Invalid zip file", 400

    # 編譯 Typst
    input_typ = os.path.join(extract_dir, entrypoint)
    if not os.path.exists(input_typ):
        return f"{entrypoint} not found in zip file", 400

    try:
        subprocess.run(['typst', 'compile', input_typ, output_path], check=True)
    except subprocess.CalledProcessError as e:
        return f"Typst compilation failed: {e}", 500

    return send_file(output_path, mimetype='application/pdf')

@app.route('/')
def index():
    return "📝 Typst ZIP + PDF 渲染服務運作中"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
