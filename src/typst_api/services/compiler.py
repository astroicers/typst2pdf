"""Typst compilation service."""

import io
import os
import shutil
import subprocess
import uuid
import zipfile
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, Union

import typst
from flask import Response, jsonify, send_file


@dataclass
class CompileOptions:
    """Compilation options."""

    output_format: str = "pdf"
    ppi: float = 144.0
    sys_inputs: Optional[Dict[str, str]] = field(default=None)


class CompilerService:
    """Service for Typst document compilation."""

    FORMAT_MIMETYPES = {
        "pdf": "application/pdf",
        "png": "image/png",
        "svg": "image/svg+xml",
    }

    def compile_and_respond(
        self, compile_kwargs: Dict[str, Any], output_format: str
    ) -> Tuple[Response, int]:
        """Run typst.compile and return a Flask response."""
        try:
            result = typst.compile(**compile_kwargs)
        except Exception as e:
            return (
                jsonify({"error": "Typst compilation failed", "details": str(e)}),
                500,
            )

        # Multi-page PNG/SVG returns list[bytes]; take first page
        if isinstance(result, list):
            if len(result) == 0:
                return jsonify({"error": "Compilation produced no output"}), 500
            result = result[0]

        mimetype = self.FORMAT_MIMETYPES[output_format]
        return (
            send_file(
                io.BytesIO(result),
                mimetype=mimetype,
                as_attachment=True,
                download_name=f"output.{output_format}",
            ),
            200,
        )

    def compile_raw(
        self, source: Union[str, bytes], options: CompileOptions
    ) -> Tuple[Response, int]:
        """Compile raw Typst source in memory."""
        compile_kwargs: Dict[str, Any] = {
            "input": source.encode("utf-8") if isinstance(source, str) else source,
            "format": options.output_format,
        }
        if options.output_format == "png":
            compile_kwargs["ppi"] = options.ppi
        if options.sys_inputs:
            compile_kwargs["sys_inputs"] = options.sys_inputs

        return self.compile_and_respond(compile_kwargs, options.output_format)

    def compile_zip(
        self, zip_file, entrypoint: str, options: CompileOptions
    ) -> Tuple[Response, int]:
        """Extract ZIP and compile Typst project."""
        file_id = str(uuid.uuid4())
        extract_dir = f"/tmp/{file_id}"
        os.makedirs(extract_dir, exist_ok=True)

        try:
            zip_path = f"{extract_dir}/upload.zip"
            zip_file.save(zip_path)

            try:
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(extract_dir)
            except zipfile.BadZipFile:
                return jsonify({"error": "Invalid zip file"}), 400

            input_typ = os.path.join(extract_dir, entrypoint)
            if not os.path.exists(input_typ):
                return (
                    jsonify(
                        {
                            "error": f"Entrypoint not found: {entrypoint}",
                            "hint": "Ensure the .typ file exists at the root of the ZIP archive",
                        }
                    ),
                    400,
                )

            compile_kwargs: Dict[str, Any] = {
                "input": input_typ,
                "root": extract_dir,
                "format": options.output_format,
            }
            if options.output_format == "png":
                compile_kwargs["ppi"] = options.ppi
            if options.sys_inputs:
                compile_kwargs["sys_inputs"] = options.sys_inputs

            return self.compile_and_respond(compile_kwargs, options.output_format)
        finally:
            shutil.rmtree(extract_dir, ignore_errors=True)

    @staticmethod
    def health_check() -> Tuple[Dict[str, str], int]:
        """Verify typst-py can compile."""
        try:
            typst.compile(b"ok")
            return {"status": "healthy", "compiler": "typst-py"}, 200
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}, 503

    @staticmethod
    def list_fonts() -> Tuple[Dict[str, Any], int]:
        """List available fonts (requires Typst CLI)."""
        try:
            result = subprocess.run(
                ["typst", "fonts"], capture_output=True, text=True, timeout=30
            )
            if result.returncode != 0:
                return {"error": "Failed to list fonts"}, 500
            fonts = [
                line.strip()
                for line in result.stdout.strip().split("\n")
                if line.strip()
            ]
            return {"fonts": fonts, "count": len(fonts)}, 200
        except (subprocess.SubprocessError, FileNotFoundError):
            return {
                "error": "Font listing requires the Typst CLI binary",
                "hint": "Install the typst CLI or use the Docker image",
            }, 503


# Singleton instance for use across routes
compiler_service = CompilerService()
