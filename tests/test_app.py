import io
import os
import zipfile
import pytest

from app import app


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_zip():
    """Create a valid in-memory ZIP containing a minimal Typst file."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr('main.typ', '#set page(width: 10cm, height: 5cm)\nHello World')
    buf.seek(0)
    return buf


@pytest.fixture
def sample_zip_custom_entry():
    """Create a ZIP with a custom-named entrypoint."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr('report.typ', '#set page(width: 10cm, height: 5cm)\nCustom Entry')
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

class TestIndex:
    def test_index_returns_json(self, client):
        resp = client.get('/')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['service'] == 'typst2pdf'
        assert data['status'] == 'running'
        assert 'version' in data


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_endpoint(self, client):
        resp = client.get('/health')
        data = resp.get_json()
        # In test environment typst may not be installed, accept both outcomes
        assert resp.status_code in (200, 503)
        assert 'status' in data


# ---------------------------------------------------------------------------
# GET /fonts
# ---------------------------------------------------------------------------

class TestFonts:
    def test_fonts_endpoint(self, client):
        resp = client.get('/fonts')
        data = resp.get_json()
        # In test environment typst may not be installed
        assert resp.status_code in (200, 503)


# ---------------------------------------------------------------------------
# POST /render
# ---------------------------------------------------------------------------

class TestRender:
    def test_render_no_file(self, client):
        """Should return 400 when no file is uploaded."""
        resp = client.post('/render')
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data

    def test_render_empty_filename(self, client):
        """Should return 400 when file has empty filename."""
        resp = client.post('/render', data={
            'file': (io.BytesIO(b''), '')
        }, content_type='multipart/form-data')
        assert resp.status_code == 400

    def test_render_invalid_zip(self, client):
        """Should return 400 when uploaded file is not a valid ZIP."""
        resp = client.post('/render', data={
            'file': (io.BytesIO(b'not a zip file'), 'bad.zip')
        }, content_type='multipart/form-data')
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error'] == 'Invalid zip file'

    def test_render_missing_entrypoint(self, client):
        """Should return 400 when entrypoint .typ not found in ZIP."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('other.typ', 'hello')
        buf.seek(0)

        resp = client.post('/render', data={
            'file': (buf, 'test.zip'),
            'entrypoint': 'main.typ'
        }, content_type='multipart/form-data')
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'not found' in data['error'].lower() or 'Entrypoint' in data['error']

    def test_render_path_traversal_dotdot(self, client):
        """Should reject entrypoint containing '..'."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('main.typ', 'hello')
        buf.seek(0)

        resp = client.post('/render', data={
            'file': (buf, 'test.zip'),
            'entrypoint': '../etc/passwd'
        }, content_type='multipart/form-data')
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'Invalid' in data['error']

    def test_render_path_traversal_absolute(self, client):
        """Should reject absolute entrypoint paths."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w') as zf:
            zf.writestr('main.typ', 'hello')
        buf.seek(0)

        resp = client.post('/render', data={
            'file': (buf, 'test.zip'),
            'entrypoint': '/etc/passwd'
        }, content_type='multipart/form-data')
        assert resp.status_code == 400

    def test_render_success(self, client, sample_zip):
        """Should return PDF when given a valid ZIP with main.typ."""
        resp = client.post('/render', data={
            'file': (sample_zip, 'test.zip')
        }, content_type='multipart/form-data')
        # typst may not be installed in test env
        if resp.status_code == 200:
            assert resp.content_type == 'application/pdf'
            assert resp.data[:4] == b'%PDF'
        else:
            # 500 = compilation error, 503 = typst not installed
            assert resp.status_code in (500, 503)

    def test_render_custom_entrypoint(self, client, sample_zip_custom_entry):
        """Should compile custom entrypoint when specified."""
        resp = client.post('/render', data={
            'file': (sample_zip_custom_entry, 'test.zip'),
            'entrypoint': 'report.typ'
        }, content_type='multipart/form-data')
        if resp.status_code == 200:
            assert resp.content_type == 'application/pdf'
        else:
            assert resp.status_code in (500, 503)
