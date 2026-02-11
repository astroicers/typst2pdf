# CLAUDE.md - typst2pdf Project Guide

## Project Overview

**typst2pdf** is a Dockerized REST API service that converts Typst documents (packaged as ZIP archives) into PDF files. Built with Python Flask and the Typst CLI compiler.

## Tech Stack

- **Language:** Python 3
- **Framework:** Flask
- **Compiler:** Typst CLI v0.13.1
- **Container:** Docker (debian:bullseye-slim)
- **Testing:** pytest

## Project Structure

```
typst2pdf/
├── app.py                  # Main Flask application with all API endpoints
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container build definition
├── tests/
│   ├── __init__.py
│   └── test_app.py         # API test suite
├── example_zip/
│   └── main.typ            # Example Typst document template
├── CLAUDE.md               # This file
└── README.md               # User-facing documentation
```

## Common Commands

### Install dependencies (local development)

```bash
pip install -r requirements.txt
```

### Run the application locally

```bash
python3 app.py
```

The server starts on `http://0.0.0.0:8000`.

### Run tests

```bash
pytest tests/ -v
```

Note: Some tests require the `typst` binary installed locally. Tests gracefully handle missing `typst` by accepting either success or the expected 500/503 status.

### Run tests without typst binary (validation-only tests)

```bash
pytest tests/ -v -k "not success and not custom_entrypoint and not health and not fonts"
```

### Build and run with Docker

```bash
docker build -t typst-api .
docker run -p 38000:8000 typst-api
```

### Test the API

```bash
cd example_zip && zip -r ../example.zip ./* && cd ..
curl -X POST http://localhost:38000/render \
  -F "file=@example.zip" \
  -F "entrypoint=main.typ" \
  --output report.pdf
```

### Lint (if flake8 is installed)

```bash
flake8 app.py tests/ --max-line-length 100
```

## API Endpoints

| Method | Path      | Description                         |
|--------|-----------|-------------------------------------|
| GET    | `/`       | Service status (JSON)               |
| GET    | `/health` | Health check with Typst version     |
| GET    | `/fonts`  | List available fonts                |
| POST   | `/render` | Render Typst ZIP to PDF             |

## Architecture Notes

- All API error responses use JSON format with an `error` field
- Temporary files are created under `/tmp/{uuid}` and cleaned up after each request
- The `entrypoint` parameter is validated against path traversal attacks
- Upload size is capped at 50MB via `MAX_CONTENT_LENGTH`
- Typst compilation has a 60-second timeout

## Key Design Decisions

- ZIP-based upload allows multi-file Typst projects (templates, images, data files)
- Stateless design: no persistent storage, each request is independent
- Docker-based deployment ensures consistent Typst version and font availability
