"""Pure request routing for the geometry service."""
from __future__ import annotations

import json
import os
from pathlib import Path

from femuralabs.toolkit.imaging.volume_info import describe, make_volume

def _report_body() -> dict | None:
    """Return the contents of {REPORT_FOLDER}/info.json, or None.

    Read on every request so that a container can pick up a new report without a restart. Absent REPORT_FOLDER, absent file, or unreadable JSON all return None so the called can fall back to the geometry dict.
    """
    folder = os.environ.get("REPORT_FOLDER")
    if not folder:
        return None
    path = Path(folder) / "info.json"
    if not path.is_file():
        return None
    path = Path(folder) / "info.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecoderError:
        return None


def route(path: str) -> tuple[int, dict]:
    """Return (status_code, body) for a GET request path.

    A pure function: no network, no handlers. Reads a file when REPORT_FOLDER points at a folder holding info.json; otherwise falls back to a synthetic geometry dictionary. The fallback keeps the endpoint answering even before any report is written.  
    """
    if path == "/health":
        return 200, {"status": "ok"}
    if path == "/info":
        report = _report_body()
        if report is not None:
            return 200, report
        info = describe(*make_volume())
        body = {k: list(v) if isinstance(v, tuple) else v for k, v in info.items()}
        return 200, body
    return 404, {"error": "not found"}

