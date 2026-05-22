import sys
sys.path.insert(0, '.')

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

class TestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        print(f"Received POST request: {path}")
        
        if path == "/api/longtask/update":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "Route matched!"}).encode())
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def log_message(self, format, *args):
        print(f"[LOG] {format % args}")

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8081), TestHandler)
    print("Test server running on http://127.0.0.1:8081")
    server.serve_forever()
