"""HTTP layer: translates the route function to a wire response."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler

from femuralabs.toolkit.service.routes import route


class Handler(BaseHTTPRequestHandler):
    """Answer each GET with the body returned by routes.route."""

    def do_GET(self):
        code, body = route(self.path)
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format, *args):
        """Silence the per-request log line; errors still go to stderr."""
        pass