"""Transparent OpenAI-compatible logging proxy.

Requests to  http://127.0.0.1:<port>/<tag>/v1/...  are forwarded to  <upstream>/v1/...
For every request one JSON line is appended to the log with timing + usage, so each agent (tag) can be
measured separately:  t_req (request received), t_first (first streamed token of any kind: reasoning,
content or tool-call), t_end, and the server-reported usage (prompt/completion tokens).
"""
import http.client
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

_log_lock = threading.Lock()


def make_server(port, upstream, log_path):
    up = urlparse(upstream)

    def log(rec):
        with _log_lock, open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def do_GET(self):
            self._proxy()

        def do_POST(self):
            self._proxy()

        def _proxy(self):
            t_req = time.time()
            parts = self.path.split("/", 2)
            tag = parts[1] if len(parts) > 1 else ""
            rest = "/" + (parts[2] if len(parts) > 2 else "")
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n) if n else b""
            req, stream = None, False
            if body:
                try:
                    req = json.loads(body)
                    stream = bool(req.get("stream"))
                    if stream:
                        req.setdefault("stream_options", {})["include_usage"] = True
                        body = json.dumps(req).encode()
                except ValueError:
                    pass
            rec = dict(tag=tag, path=rest, stream=stream, t_req=t_req,
                       n_messages=len(req.get("messages", [])) if isinstance(req, dict) else None,
                       max_tokens=req.get("max_tokens") if isinstance(req, dict) else None)
            hdrs = {k: v for k, v in self.headers.items()
                    if k.lower() not in ("host", "content-length", "connection", "accept-encoding")}
            hdrs["Content-Length"] = str(len(body))
            conn = http.client.HTTPConnection(up.hostname, up.port or 80, timeout=3600)
            try:
                conn.request(self.command, rest, body=body or None, headers=hdrs)
                resp = conn.getresponse()
                rec["status"] = resp.status
                self.send_response(resp.status)
                for k, v in resp.getheaders():
                    if k.lower() not in ("content-length", "transfer-encoding", "connection"):
                        self.send_header(k, v)
                if stream and resp.status == 200:
                    self._stream(resp, rec)
                else:
                    data = resp.read()
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    try:
                        rec["usage"] = json.loads(data).get("usage")
                    except ValueError:
                        rec["body"] = data[:500].decode("utf-8", "replace")
            except Exception as e:  # upstream failure or client hang-up
                rec["error"] = "%s: %s" % (type(e).__name__, e)
                self.close_connection = True
            finally:
                conn.close()
                rec["t_end"] = time.time()
                log(rec)

        def _stream(self, resp, rec):
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            buf, t_first, usage, finish = b"", None, None, None
            n_reason = n_content = n_tool = 0
            while True:
                chunk = resp.read1(65536)
                if not chunk:
                    break
                now = time.time()
                self.wfile.write(b"%x\r\n%s\r\n" % (len(chunk), chunk))
                self.wfile.flush()
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line.startswith(b"data:"):
                        continue
                    data = line[5:].strip()
                    if data == b"[DONE]":
                        continue
                    try:
                        ev = json.loads(data)
                    except ValueError:
                        continue
                    if ev.get("usage"):
                        usage = ev["usage"]
                    for ch in ev.get("choices") or []:
                        d = ch.get("delta") or {}
                        r, c, tc = d.get("reasoning_content") or d.get("reasoning"), d.get("content"), d.get("tool_calls")
                        if r or c or tc:
                            n_reason += bool(r); n_content += bool(c); n_tool += bool(tc)
                            if t_first is None:
                                t_first = now
                        if ch.get("finish_reason"):
                            finish = ch["finish_reason"]
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
            rec.update(t_first=t_first, usage=usage, finish=finish,
                       chunks=dict(reasoning=n_reason, content=n_content, tool=n_tool))

    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    srv.daemon_threads = True
    return srv


if __name__ == "__main__":
    import sys
    s = make_server(int(sys.argv[1]), sys.argv[2], sys.argv[3])
    print("proxy on", s.server_address, flush=True)
    s.serve_forever()
