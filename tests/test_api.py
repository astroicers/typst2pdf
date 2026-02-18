"""API test suite for typst-api."""

import io
import json
import zipfile


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------


class TestIndex:
    def test_index_returns_json(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["service"] == "typst-api"
        assert data["status"] == "running"
        assert data["version"] == "2.0.0"
        assert data["compiler"] == "typst-py"


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_returns_healthy(self, client):
        resp = client.get("/health")
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["status"] == "healthy"
        assert data["compiler"] == "typst-py"


# ---------------------------------------------------------------------------
# GET /fonts
# ---------------------------------------------------------------------------


class TestFonts:
    def test_fonts_endpoint(self, client):
        resp = client.get("/fonts")
        # Typst CLI may not be installed in test env
        assert resp.status_code in (200, 503)


# ---------------------------------------------------------------------------
# POST /render (ZIP upload)
# ---------------------------------------------------------------------------


class TestRender:
    def test_no_file(self, client):
        resp = client.post("/render")
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "No file uploaded"

    def test_empty_filename(self, client):
        resp = client.post(
            "/render",
            data={"file": (io.BytesIO(b""), "")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_invalid_zip(self, client):
        resp = client.post(
            "/render",
            data={"file": (io.BytesIO(b"not a zip"), "bad.zip")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "Invalid zip file"

    def test_missing_entrypoint(self, client):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("other.typ", "hello")
        buf.seek(0)
        resp = client.post(
            "/render",
            data={"file": (buf, "test.zip"), "entrypoint": "main.typ"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        assert "Entrypoint not found" in resp.get_json()["error"]

    def test_path_traversal_dotdot(self, client):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("main.typ", "hello")
        buf.seek(0)
        resp = client.post(
            "/render",
            data={"file": (buf, "test.zip"), "entrypoint": "../etc/passwd"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        assert "Invalid" in resp.get_json()["error"]

    def test_path_traversal_absolute(self, client):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("main.typ", "hello")
        buf.seek(0)
        resp = client.post(
            "/render",
            data={"file": (buf, "test.zip"), "entrypoint": "/etc/passwd"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_unsupported_format(self, client, sample_zip):
        resp = client.post(
            "/render",
            data={"file": (sample_zip, "test.zip"), "format": "docx"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        assert "Unsupported format" in resp.get_json()["error"]

    def test_invalid_ppi(self, client, sample_zip):
        resp = client.post(
            "/render",
            data={"file": (sample_zip, "test.zip"), "ppi": "abc"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400
        assert "ppi" in resp.get_json()["error"].lower()

    def test_invalid_sys_inputs(self, client, sample_zip):
        resp = client.post(
            "/render",
            data={"file": (sample_zip, "test.zip"), "sys_inputs": "not-json"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_render_pdf_success(self, client, sample_zip):
        resp = client.post(
            "/render",
            data={"file": (sample_zip, "test.zip")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert resp.content_type == "application/pdf"
        assert resp.data[:5] == b"%PDF-"

    def test_render_png_success(self, client, sample_zip):
        resp = client.post(
            "/render",
            data={"file": (sample_zip, "test.zip"), "format": "png"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert resp.content_type == "image/png"
        assert resp.data[:4] == b"\x89PNG"

    def test_render_svg_success(self, client, sample_zip):
        resp = client.post(
            "/render",
            data={"file": (sample_zip, "test.zip"), "format": "svg"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert "image/svg+xml" in resp.content_type
        assert b"<svg" in resp.data

    def test_render_custom_entrypoint(self, client, sample_zip_custom_entry):
        resp = client.post(
            "/render",
            data={"file": (sample_zip_custom_entry, "test.zip"), "entrypoint": "report.typ"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert resp.data[:5] == b"%PDF-"

    def test_render_multi_file(self, client, multi_file_zip):
        resp = client.post(
            "/render",
            data={"file": (multi_file_zip, "test.zip")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert resp.data[:5] == b"%PDF-"

    def test_render_with_sys_inputs(self, client):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(
                "main.typ",
                '#let name = sys.inputs.at("name", default: "nobody")\nHello #name',
            )
        buf.seek(0)
        resp = client.post(
            "/render",
            data={
                "file": (buf, "test.zip"),
                "sys_inputs": json.dumps({"name": "World"}),
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert resp.data[:5] == b"%PDF-"


# ---------------------------------------------------------------------------
# POST /render/raw
# ---------------------------------------------------------------------------


class TestRenderRaw:
    def test_no_source(self, client):
        resp = client.post(
            "/render/raw", data=json.dumps({}), content_type="application/json"
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "No source provided"

    def test_raw_pdf_json(self, client):
        resp = client.post(
            "/render/raw",
            data=json.dumps({"source": "Hello *World*"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.content_type == "application/pdf"
        assert resp.data[:5] == b"%PDF-"

    def test_raw_png_json(self, client):
        resp = client.post(
            "/render/raw",
            data=json.dumps({"source": "Hello", "format": "png", "ppi": 72}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.content_type == "image/png"
        assert resp.data[:4] == b"\x89PNG"

    def test_raw_svg_json(self, client):
        resp = client.post(
            "/render/raw",
            data=json.dumps({"source": "Hello", "format": "svg"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert "image/svg+xml" in resp.content_type
        assert b"<svg" in resp.data

    def test_raw_form_data(self, client):
        resp = client.post(
            "/render/raw",
            data={"source": "Hello *World*"},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert resp.data[:5] == b"%PDF-"

    def test_raw_with_sys_inputs_json(self, client):
        resp = client.post(
            "/render/raw",
            data=json.dumps(
                {
                    "source": '#let x = sys.inputs.at("val")\nResult: #x',
                    "sys_inputs": {"val": "42"},
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.data[:5] == b"%PDF-"

    def test_raw_with_sys_inputs_form(self, client):
        resp = client.post(
            "/render/raw",
            data={
                "source": '#let x = sys.inputs.at("val")\nResult: #x',
                "sys_inputs": json.dumps({"val": "42"}),
            },
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200

    def test_raw_unsupported_format(self, client):
        resp = client.post(
            "/render/raw",
            data=json.dumps({"source": "Hello", "format": "exe"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "Unsupported format" in resp.get_json()["error"]

    def test_raw_invalid_sys_inputs_json(self, client):
        resp = client.post(
            "/render/raw",
            data=json.dumps({"source": "Hello", "sys_inputs": "not-a-dict"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_raw_compilation_error(self, client):
        resp = client.post(
            "/render/raw",
            data=json.dumps({"source": '#import "nonexistent.typ"'}),
            content_type="application/json",
        )
        assert resp.status_code == 500
        data = resp.get_json()
        assert "error" in data
        assert "details" in data
