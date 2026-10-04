# A stand-in for the sync database, for tests only: python3 mock-db.py <port>
# Speaks the small part of the Firebase REST API the app uses: PATCH/PUT writes and a streaming GET.
import json, sys, threading, queue
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
STATE = {}; LISTEN = []; LOCK = threading.Lock()
def parts(p): return [x for x in p.split("?")[0].replace(".json", "").split("/") if x]
def get_at(ps):
    n = STATE
    for k in ps:
        if not isinstance(n, dict) or k not in n: return None
        n = n[k]
    return n
def set_at(ps, v):
    n = STATE
    for k in ps[:-1]: n = n.setdefault(k, {})
    if v is None: n.pop(ps[-1], None)
    else: n[ps[-1]] = v
class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*"); self.send_header("Access-Control-Allow-Methods", "GET, PUT, PATCH, DELETE, OPTIONS"); self.send_header("Access-Control-Allow-Headers", "*")
    def do_OPTIONS(self): self.send_response(204); self.cors(); self.send_header("Content-Length", "0"); self.end_headers()
    def reply(self, obj):
        b = json.dumps(obj).encode(); self.send_response(200); self.cors(); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        ps = parts(self.path)
        if ps == ["__state"]: return self.reply(STATE)
        if "text/event-stream" not in self.headers.get("Accept", ""): return self.reply(get_at(ps))
        q = queue.Queue()
        with LOCK: LISTEN.append((ps, q)); first = get_at(ps)
        self.send_response(200); self.cors(); self.send_header("Content-Type", "text/event-stream"); self.send_header("Cache-Control", "no-cache"); self.send_header("Connection", "close"); self.end_headers()
        try:
            self.wfile.write(("event: put\ndata: " + json.dumps({"path": "/", "data": first}) + "\n\n").encode()); self.wfile.flush()
            while True:
                try: ev, data = q.get(timeout=5)
                except queue.Empty: self.wfile.write(b"event: keep-alive\ndata: null\n\n"); self.wfile.flush(); continue
                self.wfile.write(("event: " + ev + "\ndata: " + json.dumps(data) + "\n\n").encode()); self.wfile.flush()
        except Exception: pass
        finally:
            with LOCK:
                if (ps, q) in LISTEN: LISTEN.remove((ps, q))
    def write(self, patch):
        ps = parts(self.path); body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))) or b"null")
        with LOCK:
            if patch:
                for k, v in body.items(): set_at(ps + [x for x in k.split("/") if x], v)
            else: set_at(ps, body)
            for lp, q in LISTEN:
                if ps[:len(lp)] == lp: q.put(("patch" if patch else "put", {"path": "/" + "/".join(ps[len(lp):]), "data": body}))
        self.reply(body)
    def do_PATCH(self): self.write(True)
    def do_PUT(self): self.write(False)
ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
