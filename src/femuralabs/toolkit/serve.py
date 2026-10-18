"""Start the geometry service; port comes from PORT, default 8000."""
from __future__ import annotations

import os
from http.server import HTTPServer

from femuralabs.toolkit.api import Handler


def main() -> int:
    """Bind to 0.0.0.0 so a port published by Docker can reach the server."""
    port = int(os.environ.get("PORT", "8000"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"serving on 0.0.0.0:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())