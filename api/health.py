import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        backend_url = os.environ.get("RENDER_API_URL", "").rstrip("/")
        if not backend_url:
            self._send_json(
                503,
                {"detail": "Set the RENDER_API_URL Vercel environment variable."},
            )
            return

        request = Request(f"{backend_url}/health", method="GET")
        try:
            with urlopen(request, timeout=10) as response:
                self._send_response(
                    response.status,
                    response.headers.get("Content-Type", "application/json"),
                    response.read(),
                )
        except HTTPError as exc:
            self._send_response(
                exc.code,
                exc.headers.get("Content-Type", "application/json"),
                exc.read(),
            )
        except URLError:
            self._send_json(
                502,
                {"detail": "The Render analysis service could not be reached."},
            )

    def _send_json(self, status, payload):
        self._send_response(
            status,
            "application/json",
            json.dumps(payload).encode("utf-8"),
        )

    def _send_response(self, status, content_type, body):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
