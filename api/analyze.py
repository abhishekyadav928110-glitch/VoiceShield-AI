import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        backend_url = os.environ.get("RENDER_API_URL", "").rstrip("/")
        if not backend_url:
            self._send_json(
                503,
                {"detail": "Set the RENDER_API_URL Vercel environment variable."},
            )
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._send_json(400, {"detail": "Invalid request content length."})
            return

        if content_length <= 0:
            self._send_json(400, {"detail": "No audio file was provided."})
            return

        body = self.rfile.read(content_length)
        request = Request(
            f"{backend_url}/api/analyze",
            data=body,
            headers={
                "Content-Type": self.headers.get(
                    "Content-Type",
                    "application/octet-stream",
                ),
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=55) as response:
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
        except TimeoutError:
            self._send_json(504, {"detail": "The audio analysis request timed out."})
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
