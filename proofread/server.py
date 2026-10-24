import json, os, queue, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
os.chdir(HERE)  # Memory() defaults to ./memory.jsonl
from agent import solve

DONE = object()

class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, kind):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/":
            self.send(200, (HERE / "ui/index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/memory":
            mem = Path("memory.jsonl")
            rows = [json.loads(l) for l in mem.read_text().splitlines() if l.strip()] if mem.exists() else []
            self.send(200, json.dumps(rows).encode(), "application/json")
        else:
            self.send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path != "/solve":
            return self.send(404, b"not found", "text/plain")
        try:
            problem = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))["problem"].strip()
            assert problem
        except (ValueError, KeyError, TypeError, AttributeError, AssertionError):
            return self.send(400, b'{"error":"expected {\\"problem\\": str}"}', "application/json")

        events = queue.Queue()
        def work():
            try:
                answer, verified = solve(problem, log=lambda text: events.put({"type": "log", "text": text}))
                events.put({"type": "done", "answer": answer, "verified": verified})
            except Exception as e:
                events.put({"type": "done", "answer": None, "verified": False, "error": str(e)})
            events.put(DONE)
        threading.Thread(target=work, daemon=True).start()

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        while (event := events.get()) is not DONE:
            try:
                self.wfile.write(f"data: {json.dumps(event)}\n\n".encode())
                self.wfile.flush()
            except BrokenPipeError:
                return

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8765))
    print(f"Proofread on http://localhost:{port}")
    ThreadingHTTPServer(("", port), Handler).serve_forever()
