"""typst-api - REST API for Typst document conversion."""

__version__ = "2.0.0"

from flask import Flask


def create_app(config_name: str = "default") -> Flask:
    """Application factory pattern."""
    from .config import get_config
    from .routes.health import health_bp
    from .routes.render import render_bp

    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(render_bp)

    return app


def main():
    """CLI entry point."""
    app = create_app()
    app.run(host="0.0.0.0", port=8000)
