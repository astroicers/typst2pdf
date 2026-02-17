# CLAUDE.md - typst2pdf Project Guide

## Project Overview

**typst2pdf** is a Dockerized REST API service that converts Typst documents into PDF, PNG, and SVG files. Built with Python Flask and [typst-py](https://github.com/messense/typst-py) (native Python binding to the Typst compiler).

## Tech Stack

- **Language:** Python 3
- **Framework:** Flask
- **Compiler:** typst-py (native binding, no subprocess)
- **Container:** Docker (python:3.12-slim)
- **Testing:** pytest (28 tests)

## Project Structure

```
typst2pdf/
├── app.py                  # Main Flask application with all API endpoints
├── requirements.txt        # Python dependencies (flask, typst, pytest)
├── Dockerfile              # Container build definition
├── tests/
│   ├── __init__.py
│   └── test_app.py         # API test suite (28 tests)
├── example_zip/
│   └── main.typ            # Example Typst document template
├── .claude/
│   └── settings.json       # SessionStart hook
├── CLAUDE.md               # This file
└── README.md               # User-facing documentation with full API reference
```

## Common Commands

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the application

```bash
python3 app.py
```

The server starts on `http://0.0.0.0:8000`.

### Run tests

```bash
pytest tests/ -v
```

All 28 tests should pass. Tests use typst-py directly (no external binary needed).

### Build and run with Docker

```bash
docker build -t typst-api .
docker run -p 38000:8000 typst-api
```

### Test the API (ZIP upload)

```bash
cd example_zip && zip -r ../example.zip ./* && cd ..
curl -X POST http://localhost:38000/render \
  -F "file=@example.zip" \
  -F "entrypoint=main.typ" \
  --output report.pdf
```

### Test the API (raw source)

```bash
curl -X POST http://localhost:38000/render/raw \
  -H "Content-Type: application/json" \
  -d '{"source": "= Hello World"}' \
  --output output.pdf
```

### Lint (if flake8 is installed)

```bash
flake8 app.py tests/ --max-line-length 100
```

## API Endpoints

| Method | Path           | Description                          |
|--------|----------------|--------------------------------------|
| GET    | `/`            | Service status (JSON)                |
| GET    | `/health`      | Health check (typst-py verification) |
| GET    | `/fonts`       | List available fonts (needs CLI)     |
| POST   | `/render`      | Render Typst ZIP to PDF/PNG/SVG      |
| POST   | `/render/raw`  | Render raw Typst source to PDF/PNG/SVG |

## Key Features

- **typst-py native binding:** No subprocess calls for compilation — direct Rust FFI
- **Multi-format output:** PDF, PNG, SVG via `format` parameter
- **In-memory compilation:** `/render/raw` compiles entirely in memory (zero disk I/O)
- **sys_inputs:** Pass dynamic data into Typst templates at compile time
- **Multi-file projects:** ZIP upload preserves imports, images, data files
- **Path traversal protection:** Entrypoint validated against `..` and absolute paths
- **Temp file cleanup:** ZIP extractions cleaned up in `finally` blocks
- **50MB upload limit:** Configurable via `MAX_CONTENT_LENGTH`

## Architecture Notes

- All API error responses use JSON format with an `error` field
- `/render` extracts ZIP to `/tmp/{uuid}`, compiles via file path, cleans up
- `/render/raw` compiles bytes directly in memory — no temp files
- `/fonts` still uses subprocess (Typst CLI) since typst-py has no font listing API
- PNG/SVG for multi-page documents returns first page only
