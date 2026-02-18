"""Render routes for Typst compilation."""

from flask import Blueprint, jsonify, request

from ..services.compiler import CompileOptions, compiler_service
from ..utils.parsers import VALID_FORMATS, parse_format, parse_ppi, parse_sys_inputs

render_bp = Blueprint("render", __name__)


@render_bp.route("/render", methods=["POST"])
def render_typst():
    """Render a Typst ZIP project to PDF/PNG/SVG.

    Form parameters:
        file:        ZIP archive containing .typ files (required)
        entrypoint:  Main .typ file in the ZIP (default: main.typ)
        format:      Output format - pdf, png, svg (default: pdf)
        ppi:         Pixels per inch for PNG output (default: 144.0)
        sys_inputs:  JSON object of key-value strings passed to Typst
    """
    # --- file validation ---
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded", "field": "file"}), 400

    zip_file = request.files["file"]
    if zip_file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    entrypoint = request.form.get("entrypoint", "main.typ")
    if ".." in entrypoint or entrypoint.startswith("/"):
        return jsonify({"error": "Invalid entrypoint path"}), 400

    # --- parameter parsing ---
    output_format, bad_fmt = parse_format(request.form.get("format"))
    if bad_fmt:
        return (
            jsonify(
                {"error": f"Unsupported format: {bad_fmt}", "supported": list(VALID_FORMATS)}
            ),
            400,
        )

    ppi_value, bad_ppi = parse_ppi(request.form.get("ppi"))
    if bad_ppi is not None:
        return jsonify({"error": f"Invalid ppi value: {bad_ppi}"}), 400

    sys_inputs, si_err = parse_sys_inputs(request.form.get("sys_inputs"))
    if si_err:
        return jsonify({"error": si_err}), 400

    options = CompileOptions(
        output_format=output_format,
        ppi=ppi_value,
        sys_inputs=sys_inputs,
    )

    return compiler_service.compile_zip(zip_file, entrypoint, options)


@render_bp.route("/render/raw", methods=["POST"])
def render_raw():
    """Render raw Typst source code to PDF/PNG/SVG (no ZIP needed).

    Accepts JSON body:
        {
            "source":     "Hello *World*",          // required
            "format":     "pdf",                    // optional, default: pdf
            "ppi":        144.0,                    // optional, for PNG
            "sys_inputs": {"name": "value"}         // optional
        }

    Also accepts form data:
        source:      Typst source code (required)
        format:      pdf | png | svg (default: pdf)
        ppi:         float (default: 144.0)
        sys_inputs:  JSON string
    """
    # --- parse input from JSON or form data ---
    if request.is_json:
        body = request.get_json(silent=True) or {}
        source = body.get("source")
        fmt_raw = body.get("format", "pdf")
        ppi_raw = body.get("ppi", 144.0)
        si_raw = body.get("sys_inputs")
        # sys_inputs already a dict from JSON
        if si_raw is not None:
            if not isinstance(si_raw, dict):
                return jsonify({"error": "sys_inputs must be a JSON object"}), 400
            sys_inputs = {str(k): str(v) for k, v in si_raw.items()}
        else:
            sys_inputs = None
        si_err = None
    else:
        source = request.form.get("source")
        fmt_raw = request.form.get("format", "pdf")
        ppi_raw = request.form.get("ppi", "144.0")
        sys_inputs, si_err = parse_sys_inputs(request.form.get("sys_inputs"))

    if not source:
        return jsonify({"error": "No source provided", "field": "source"}), 400

    output_format, bad_fmt = parse_format(fmt_raw)
    if bad_fmt:
        return (
            jsonify(
                {"error": f"Unsupported format: {bad_fmt}", "supported": list(VALID_FORMATS)}
            ),
            400,
        )

    ppi_value, bad_ppi = parse_ppi(ppi_raw)
    if bad_ppi is not None:
        return jsonify({"error": f"Invalid ppi value: {bad_ppi}"}), 400

    if si_err:
        return jsonify({"error": si_err}), 400

    options = CompileOptions(
        output_format=output_format,
        ppi=ppi_value,
        sys_inputs=sys_inputs,
    )

    return compiler_service.compile_raw(source, options)
