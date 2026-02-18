"""Health and status routes."""

from flask import Blueprint, jsonify

from ..services.compiler import compiler_service

health_bp = Blueprint("health", __name__)


@health_bp.route("/")
def index():
    """Service status."""
    return jsonify(
        {
            "service": "typst-api",
            "status": "running",
            "version": "2.0.0",
            "compiler": "typst-py",
        }
    )


@health_bp.route("/health", methods=["GET"])
def health():
    """Health check - verifies typst-py can compile."""
    data, status_code = compiler_service.health_check()
    return jsonify(data), status_code


@health_bp.route("/fonts", methods=["GET"])
def list_fonts():
    """List available fonts (requires Typst CLI binary)."""
    data, status_code = compiler_service.list_fonts()
    return jsonify(data), status_code
