# CLAUDE.md - typst-api Project Guide

## Project Overview

**typst-api** is a Dockerized REST API service that converts Typst documents into PDF, PNG, and SVG files. Built with Python Flask and [typst-py](https://github.com/messense/typst-py) (native Python binding to the Typst compiler).

## Tech Stack

- **Language:** Python 3
- **Framework:** Flask (Application Factory pattern)
- **Compiler:** typst-py (native binding, no subprocess)
- **Container:** Docker (python:3.12-slim)
- **Testing:** pytest (28 tests)
- **Packaging:** pyproject.toml (PEP 621)

## Project Structure

```
typst-api/
├── pyproject.toml              # Python packaging configuration
├── Dockerfile                  # Container build definition
├── README.md                   # User-facing documentation
├── CLAUDE.md                   # This file
├── src/
│   └── typst_api/
│       ├── __init__.py         # create_app factory, main entry point
│       ├── config.py           # Configuration classes
│       ├── services/
│       │   ├── __init__.py
│       │   └── compiler.py     # Typst compilation service
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── health.py       # GET /, /health, /fonts
│       │   └── render.py       # POST /render, /render/raw
│       └── utils/
│           ├── __init__.py
│           └── parsers.py      # Input parsing/validation
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # pytest fixtures
│   └── test_api.py             # API test suite (28 tests)
├── example_zip/
│   └── main.typ                # Example Typst document template
└── .claude/
    └── settings.json           # SessionStart hook
```

## Common Commands

### Install for development

```bash
pip install -e .
```

### Run the application

```bash
typst-api
```

Or using Python directly:

```bash
python -c "from typst_api import main; main()"
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
flake8 src/typst_api tests/ --max-line-length 100
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

- Uses Flask Application Factory pattern (`create_app`)
- Routes are organized into Blueprints (health_bp, render_bp)
- Business logic extracted to CompilerService class
- Configuration supports multiple environments (development, testing, production)
- All API error responses use JSON format with an `error` field
- `/render` extracts ZIP to `/tmp/{uuid}`, compiles via file path, cleans up
- `/render/raw` compiles bytes directly in memory — no temp files
- `/fonts` still uses subprocess (Typst CLI) since typst-py has no font listing API
- PNG/SVG for multi-page documents returns first page only
