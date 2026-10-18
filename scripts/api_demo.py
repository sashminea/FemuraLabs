"""Start the geometry service in a thread and call it three times."""
import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer

from femuralabs.toolkit.api import Handler


def main() -> int:
    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    for path in ("/health", "/info", "/missing"):
        try:
            reply = urllib.request.urlopen(base + path)
        except urllib.error.HTTPError as error:
            reply = error
        print(path, reply.getcode(), json.loads(reply.read()))
    server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())