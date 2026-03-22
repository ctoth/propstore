"""Tiny HTTP server that receives a PDF POST and saves it."""
import http.server
import sys
import os

OUTPUT_PATH = sys.argv[1] if len(sys.argv) > 1 else "paper.pdf"

class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length)
        with open(OUTPUT_PATH, "wb") as f:
            f.write(data)
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(b"OK")
        print(f"Saved {len(data)} bytes to {OUTPUT_PATH}")
        # Shut down after receiving
        os._exit(0)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

server = http.server.HTTPServer(("127.0.0.1", 18923), Handler)
print(f"Listening on http://127.0.0.1:18923 — will save to {OUTPUT_PATH}")
server.serve_forever()
