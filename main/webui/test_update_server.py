import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

LOOPCLI_ROOT = Path("D:/loopcli")

class UpdateHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/api/longtask/update":
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8', errors='ignore'))
            content = data.get('content', '')
            
            longtask_file = LOOPCLI_ROOT / "longtask.md"
            longtask_file.write_text(content, encoding='utf-8')
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            response = {"status": "updated", "message": "长期任务已更新"}
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[LOG] {format % args}")

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8082), UpdateHandler)
    print("Test update server running on http://127.0.0.1:8082")
    server.serve_forever()
