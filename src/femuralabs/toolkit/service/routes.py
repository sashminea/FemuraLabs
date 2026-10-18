"""Pure request routing for the geometry service."""
from __future__ import annotations

from femuralabs.toolkit.volume_info import describe, make_volume


def route(path: str) -> tuple[int, dict]:
    """Return (status_code, body) for a GET request path.

    A pure function: no network, no files, no global state. The HTTP handler
    in api.py calls it and translates the result to bytes. This is what makes
    the routing testable without starting a server.
    """
    if path == "/health":
        return 200, {"status": "ok"}
    if path == "/info":
        info = describe(*make_volume())
        # Convert tuples to lists so the returned dict is JSON-ready as-is:
        # the contract of this function is "returns a dict that json.dumps
        # can serialise", and a test can assert either shape without surprise.
        body = {k: list(v) if isinstance(v, tuple) else v for k, v in info.items()}
        return 200, body
    return 404, {"error": "not found"}