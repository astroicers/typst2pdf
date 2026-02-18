"""Input parsing and validation utilities."""

import json
from typing import Dict, Optional, Set, Tuple

VALID_FORMATS: Set[str] = {"pdf", "png", "svg"}

FORMAT_MIMETYPES: Dict[str, str] = {
    "pdf": "application/pdf",
    "png": "image/png",
    "svg": "image/svg+xml",
}


def parse_format(value: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Validate and return output format.

    Returns:
        (format, None) on success
        (None, bad_format) on failure
    """
    fmt = (value or "pdf").lower()
    if fmt not in VALID_FORMATS:
        return None, fmt
    return fmt, None


def parse_ppi(value) -> Tuple[Optional[float], Optional[str]]:
    """Validate and return PPI value.

    Returns:
        (ppi_value, None) on success
        (None, bad_value) on failure
    """
    try:
        return float(value if value is not None else 144.0), None
    except (ValueError, TypeError):
        return None, str(value)


def parse_sys_inputs(
    raw: Optional[str],
) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    """Parse and validate sys_inputs JSON string.

    Returns:
        (sys_inputs_dict, None) on success
        (None, error_message) on failure
    """
    if not raw:
        return None, None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, "Invalid JSON in sys_inputs"
    if not isinstance(data, dict):
        return None, "sys_inputs must be a JSON object"
    return {str(k): str(v) for k, v in data.items()}, None
