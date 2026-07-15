"""Huobz AI Library — minimal working entrypoint."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = {
            "ok": True,
            "service": "HuobzAl",
            "title": "Huobz AI Library",
            "description": "Shared AI utilities library (prompts, adapters) consumed by HuobzAi/HuobzEdge — not a full agent OS.",
            "health": "pass",
        }
        data = json.dumps(body, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):  # quiet
        return


def main() -> None:
    port = 8765
    print(f"Huobz AI Library listening on http://127.0.0.1:{port}")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
