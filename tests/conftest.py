"""Pytest fixtures for typst-api tests."""

import io
import zipfile

import pytest

from typst_api import create_app


@pytest.fixture
def app():
    """Create application for testing."""
    return create_app("testing")


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_zip():
    """Create a valid in-memory ZIP containing a minimal Typst file."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("main.typ", "#set page(width: 10cm, height: 5cm)\nHello World")
    buf.seek(0)
    return buf


@pytest.fixture
def sample_zip_custom_entry():
    """Create a ZIP with a custom-named entrypoint."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("report.typ", "#set page(width: 10cm, height: 5cm)\nCustom Entry")
    buf.seek(0)
    return buf


@pytest.fixture
def multi_file_zip():
    """Create a ZIP with multiple Typst files (import)."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("main.typ", '#import "lib.typ": greet\n#greet("World")')
        zf.writestr("lib.typ", "#let greet(name) = [Hello, #name!]")
    buf.seek(0)
    return buf
