"""Minimal Ollama-compatible development shim.

This server only implements POST /api/generate and returns a deterministic
response so the local multiagent runtime can be exercised without a real model.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/generate":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        payload = json.loads(body.decode("utf-8"))
        response = {
            "response": json.dumps(
                {
                    "model": payload.get("model"),
                    "prompt": payload.get("prompt"),
                    "mode": "dev-shim",
                },
                ensure_ascii=True,
            )
        }
        encoded = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 11434), Handler)
    print("fake_ollama_server listening on http://127.0.0.1:11434", flush=True)
    server.serve_forever()