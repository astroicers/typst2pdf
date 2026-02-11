# typst2pdf

Dockerized REST API service for converting [Typst](https://typst.app/) documents to PDF.

Upload a ZIP archive containing your Typst source files, and receive the compiled PDF back.

## Quick Start

### Build & Run (Docker)

```bash
docker build -t typst-api .
docker run -p 38000:8000 typst-api
```

The service is now available at `http://localhost:38000`.

### Local Development

```bash
pip install -r requirements.txt
python3 app.py
# Server starts on http://localhost:8000
```

### Run Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

---

## API Reference

### `GET /` — Service Status

Returns service metadata and running status.

**Response:**

```json
{
  "service": "typst2pdf",
  "status": "running",
  "version": "1.0.0"
}
```

| Status Code | Description       |
|-------------|-------------------|
| 200         | Service is running |

---

### `GET /health` — Health Check

Verifies the Typst compiler is available and returns its version.

**Response (healthy):**

```json
{
  "status": "healthy",
  "typst_version": "typst 0.13.1"
}
```

**Response (unhealthy):**

```json
{
  "status": "unhealthy",
  "error": "Typst compiler not available"
}
```

| Status Code | Description                |
|-------------|----------------------------|
| 200         | Typst compiler is available |
| 503         | Typst compiler unavailable  |

---

### `GET /fonts` — List Available Fonts

Returns all fonts available in the runtime environment.

**Response:**

```json
{
  "fonts": ["Noto Sans", "Noto Sans CJK TC", "..."],
  "count": 42
}
```

| Status Code | Description                |
|-------------|----------------------------|
| 200         | Font list returned          |
| 500         | Failed to list fonts        |
| 503         | Typst compiler unavailable  |

---

### `POST /render` — Render Typst to PDF

Upload a ZIP archive containing `.typ` files and receive the compiled PDF.

**Content-Type:** `multipart/form-data`

**Parameters:**

| Parameter    | Type   | Required | Default    | Description                              |
|-------------|--------|----------|------------|------------------------------------------|
| `file`      | file   | Yes      | —          | ZIP archive containing Typst source files |
| `entrypoint`| string | No       | `main.typ` | Path to the main `.typ` file in the ZIP   |

**Success Response:**

- **Status:** `200 OK`
- **Content-Type:** `application/pdf`
- **Body:** The compiled PDF file

**Error Responses:**

| Status Code | Error                    | Description                                     |
|-------------|--------------------------|--------------------------------------------------|
| 400         | No file uploaded         | The `file` field is missing                      |
| 400         | Empty filename           | The uploaded file has no filename                |
| 400         | Invalid entrypoint path  | Entrypoint contains `..` or starts with `/`      |
| 400         | Invalid zip file         | The uploaded file is not a valid ZIP archive     |
| 400         | Entrypoint not found     | The specified `.typ` file was not found in the ZIP |
| 500         | Typst compilation failed | Typst returned a compilation error (details included) |
| 500         | PDF output not generated | Compilation succeeded but no output file was created |

**Example — curl:**

```bash
# Prepare a ZIP from your Typst project
cd my_typst_project/
zip -r ../project.zip ./*

# Send to the API
curl -X POST http://localhost:38000/render \
  -F "file=@../project.zip" \
  -F "entrypoint=main.typ" \
  --output output.pdf
```

**Example — Python (requests):**

```python
import requests

with open('project.zip', 'rb') as f:
    resp = requests.post(
        'http://localhost:38000/render',
        files={'file': ('project.zip', f, 'application/zip')},
        data={'entrypoint': 'main.typ'}
    )

if resp.status_code == 200:
    with open('output.pdf', 'wb') as pdf:
        pdf.write(resp.content)
else:
    print(resp.json())
```

**Example — JavaScript (fetch):**

```javascript
const formData = new FormData();
formData.append('file', zipBlob, 'project.zip');
formData.append('entrypoint', 'main.typ');

const resp = await fetch('http://localhost:38000/render', {
  method: 'POST',
  body: formData,
});

if (resp.ok) {
  const blob = await resp.blob();
  // Use the PDF blob
} else {
  const error = await resp.json();
  console.error(error);
}
```

---

## Limits & Constraints

| Limit               | Value  |
|----------------------|--------|
| Max upload size      | 50 MB  |
| Compilation timeout  | 60 sec |
| Container port       | 8000   |

## Fonts

The Docker image ships with the following font families:

- **Noto Sans / Serif** (including CJK variants for Chinese, Japanese, Korean)
- **Linux Libertine**

Use `GET /fonts` to see the full list at runtime.

To check fonts inside the container:

```bash
docker exec <container_id> typst fonts
```

## Example Template

The `example_zip/` directory contains a sample Typst document. To test:

```bash
cd example_zip
zip -r ../example.zip ./*
curl -X POST http://localhost:38000/render \
  -F "file=@../example.zip" \
  -F "entrypoint=main.typ" \
  --output report.pdf
```

## Project Structure

```
typst2pdf/
├── app.py                  # Flask application
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container build
├── tests/
│   └── test_app.py         # Test suite
├── example_zip/
│   └── main.typ            # Example Typst template
├── CLAUDE.md               # Claude Code project guide
└── README.md               # This file
```

## License

See repository for license information.
