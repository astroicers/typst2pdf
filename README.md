# typst2pdf

Dockerized REST API service for converting [Typst](https://typst.app/) documents to PDF, PNG, and SVG.

Powered by [typst-py](https://github.com/messense/typst-py) — a native Python binding to the Typst compiler. No subprocess calls, in-memory compilation, multi-format output.

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

Returns service metadata.

**Response:**

```json
{
  "service": "typst2pdf",
  "status": "running",
  "version": "2.0.0",
  "compiler": "typst-py"
}
```

---

### `GET /health` — Health Check

Verifies the typst-py compiler can compile.

**Response (healthy):**

```json
{
  "status": "healthy",
  "compiler": "typst-py"
}
```

| Status Code | Description                |
|-------------|----------------------------|
| 200         | Compiler is working         |
| 503         | Compiler unavailable        |

---

### `GET /fonts` — List Available Fonts

Returns all fonts available in the runtime environment. Requires the Typst CLI binary (included in Docker image).

**Response:**

```json
{
  "fonts": ["Noto Sans", "Noto Sans CJK TC", "..."],
  "count": 42
}
```

| Status Code | Description                     |
|-------------|---------------------------------|
| 200         | Font list returned               |
| 503         | Typst CLI not available          |

---

### `POST /render` — Render ZIP Project

Upload a ZIP archive containing `.typ` files and receive the compiled output.

**Content-Type:** `multipart/form-data`

**Parameters:**

| Parameter    | Type   | Required | Default    | Description                                          |
|-------------|--------|----------|------------|------------------------------------------------------|
| `file`      | file   | Yes      | —          | ZIP archive containing Typst source files             |
| `entrypoint`| string | No       | `main.typ` | Path to the main `.typ` file in the ZIP               |
| `format`    | string | No       | `pdf`      | Output format: `pdf`, `png`, or `svg`                 |
| `ppi`       | number | No       | `144.0`    | Pixels per inch (PNG only)                            |
| `sys_inputs`| string | No       | —          | JSON object of key-value strings passed into Typst    |

**Success Response:**

| Format | Content-Type      | Description           |
|--------|-------------------|-----------------------|
| pdf    | application/pdf   | PDF document          |
| png    | image/png         | PNG image (1st page)  |
| svg    | image/svg+xml     | SVG image (1st page)  |

**Error Responses:**

| Status | Error                    | Description                                      |
|--------|--------------------------|--------------------------------------------------|
| 400    | No file uploaded         | The `file` field is missing                      |
| 400    | Empty filename           | The uploaded file has no filename                 |
| 400    | Invalid entrypoint path  | Entrypoint contains `..` or starts with `/`      |
| 400    | Invalid zip file         | Not a valid ZIP archive                          |
| 400    | Entrypoint not found     | Specified `.typ` file not found in ZIP           |
| 400    | Unsupported format       | Format is not pdf/png/svg                        |
| 400    | Invalid ppi value        | PPI is not a valid number                        |
| 400    | Invalid JSON             | sys_inputs is not valid JSON                     |
| 500    | Compilation failed       | Typst returned an error (details included)       |

**Example — curl (PDF):**

```bash
cd my_typst_project/
zip -r ../project.zip ./*

curl -X POST http://localhost:38000/render \
  -F "file=@../project.zip" \
  -F "entrypoint=main.typ" \
  --output output.pdf
```

**Example — curl (PNG):**

```bash
curl -X POST http://localhost:38000/render \
  -F "file=@project.zip" \
  -F "format=png" \
  -F "ppi=300" \
  --output output.png
```

**Example — curl (with sys_inputs):**

```bash
curl -X POST http://localhost:38000/render \
  -F "file=@project.zip" \
  -F 'sys_inputs={"company":"ACME","date":"2025-01-01"}' \
  --output output.pdf
```

**Example — Python:**

```python
import requests

with open('project.zip', 'rb') as f:
    resp = requests.post(
        'http://localhost:38000/render',
        files={'file': ('project.zip', f, 'application/zip')},
        data={
            'entrypoint': 'main.typ',
            'format': 'pdf',
            'sys_inputs': '{"company": "ACME"}'
        }
    )

if resp.status_code == 200:
    with open('output.pdf', 'wb') as pdf:
        pdf.write(resp.content)
else:
    print(resp.json())
```

---

### `POST /render/raw` — Render Raw Typst Source

Compile Typst source code directly — no ZIP packaging needed. Ideal for single-file documents, previews, and programmatic generation.

**Accepts JSON or form data.**

#### JSON Body

```json
{
  "source":     "= Hello\nThis is *bold*.",
  "format":     "pdf",
  "ppi":        144.0,
  "sys_inputs": {"name": "World"}
}
```

| Field        | Type   | Required | Default | Description                           |
|-------------|--------|----------|---------|---------------------------------------|
| `source`    | string | Yes      | —       | Typst source code                     |
| `format`    | string | No       | `pdf`   | Output format: `pdf`, `png`, `svg`    |
| `ppi`       | number | No       | `144.0` | Pixels per inch (PNG only)            |
| `sys_inputs`| object | No       | —       | Key-value strings passed into Typst   |

#### Form Data

| Parameter    | Type   | Required | Default | Description                        |
|-------------|--------|----------|---------|------------------------------------|
| `source`    | string | Yes      | —       | Typst source code                  |
| `format`    | string | No       | `pdf`   | Output format: `pdf`, `png`, `svg` |
| `ppi`       | string | No       | `144.0` | Pixels per inch (PNG only)         |
| `sys_inputs`| string | No       | —       | JSON string of key-value pairs     |

**Example — curl (JSON):**

```bash
curl -X POST http://localhost:38000/render/raw \
  -H "Content-Type: application/json" \
  -d '{"source": "= Hello World\nThis is a *test*."}' \
  --output output.pdf
```

**Example — curl (PNG preview):**

```bash
curl -X POST http://localhost:38000/render/raw \
  -H "Content-Type: application/json" \
  -d '{"source": "= Preview", "format": "png", "ppi": 300}' \
  --output preview.png
```

**Example — curl (with sys_inputs):**

```bash
curl -X POST http://localhost:38000/render/raw \
  -H "Content-Type: application/json" \
  -d '{
    "source": "#let name = sys.inputs.at(\"name\")\nHello, #name!",
    "sys_inputs": {"name": "Alice"}
  }' \
  --output output.pdf
```

**Example — JavaScript (fetch):**

```javascript
const resp = await fetch('http://localhost:38000/render/raw', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    source: '= Report\nGenerated at ' + new Date().toISOString(),
    format: 'pdf',
  }),
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

## Using `sys_inputs` for Dynamic Templates

`sys_inputs` lets you pass key-value data into Typst at compile time, enabling dynamic document generation without modifying the `.typ` source.

**Typst template (`main.typ`):**

```typst
#let data = json(bytes(sys.inputs.at("data")))

= Report for #data.company

Date: #data.date
Author: #data.author
```

**API call:**

```bash
curl -X POST http://localhost:38000/render \
  -F "file=@template.zip" \
  -F 'sys_inputs={"data": "{\"company\":\"ACME\",\"date\":\"2025-01-01\",\"author\":\"Alice\"}"}' \
  --output report.pdf
```

---

## Limits & Constraints

| Limit               | Value  |
|----------------------|--------|
| Max upload size      | 50 MB  |
| Container port       | 8000   |

## Fonts

The Docker image ships with:

- **Noto Sans / Serif** (including CJK variants for Chinese, Japanese, Korean)
- **Linux Libertine**

Use `GET /fonts` to see the full list at runtime.

## Example Template

The `example_zip/` directory contains a sample Typst document:

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
├── app.py                  # Flask application (typst-py compiler)
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container build
├── tests/
│   └── test_app.py         # 28 tests
├── example_zip/
│   └── main.typ            # Example Typst template
├── CLAUDE.md               # Claude Code project guide
└── README.md               # This file
```

## Architecture

```
Client                          typst2pdf (Flask)
  │                                   │
  │  POST /render/raw                 │
  │  { "source": "..." }  ───────▶  typst.compile(bytes)
  │                                   │  (in-memory, no disk I/O)
  │  ◀──── PDF/PNG/SVG bytes ─────   │
  │                                   │
  │  POST /render                     │
  │  [ZIP file] ──────────────────▶  extract → typst.compile(path)
  │                                   │  (disk-based for multi-file)
  │  ◀──── PDF/PNG/SVG bytes ─────   │
```

## License

See repository for license information.
