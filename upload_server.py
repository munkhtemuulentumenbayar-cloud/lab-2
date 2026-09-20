#!/usr/bin/env python3
"""Minimal file-upload server so renders can reach the sandbox directly."""
import cgi
import os
import html
from http.server import BaseHTTPRequestHandler, HTTPServer

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Upload render</title>
<style>
  body { font-family: system-ui, sans-serif; background:#0A0F1A; color:#E0F9FF;
         display:flex; align-items:center; justify-content:center; min-height:100vh; margin:0; }
  .card { background:#162434; border:1px solid #39FFB0; border-radius:14px;
          padding:34px 38px; max-width:520px; width:100%; box-shadow:0 0 40px rgba(57,255,176,.15); }
  h1 { color:#7DEBFF; font-size:22px; margin:0 0 6px; }
  p  { color:#9fd4dd; font-size:14px; line-height:1.5; }
  input[type=file] { margin:18px 0; color:#E0F9FF; }
  button { background:#39FFB0; color:#06121a; border:0; border-radius:8px;
           padding:12px 20px; font-size:15px; font-weight:700; cursor:pointer; }
  button:hover { background:#7DEBFF; }
  .ok { color:#39FFB0; }
  .err { color:#ff7b7b; }
  .hint { color:#7a9aa6; font-size:12px; margin-top:14px; }
</style>
</head>
<body>
  <div class="card">
    <h1>Arctic Lens — render upload</h1>
    <p>Choose the render file (PNG) to send to the workspace. The agent will
       style it into the Cyber-Glacial look right away.</p>
    <form method="post" enctype="multipart/form-data" action="/">
      <input type="file" name="file" accept="image/png,image/jpeg,.png,.jpg,.jpeg">
      <br><button type="submit">Upload</button>
    </form>
    <div class="hint">Files are saved to the workspace uploads/ folder.</div>
  </div>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _write(self, code, body, ctype="text/html; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._write(200, PAGE.encode())

    def do_POST(self):
        ctype = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in ctype:
            self._write(400, b"Expected multipart/form-data")
            return
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": ctype},
        )
        items = form["file"]
        if not isinstance(items, list):
            items = [items]
        saved = []
        for item in items:
            if not item.file:
                continue
            fn = os.path.basename(item.filename) or "upload.bin"
            dest = os.path.join(UPLOAD_DIR, fn)
            with open(dest, "wb") as out:
                while True:
                    chunk = item.file.read(65536)
                    if not chunk:
                        break
                    out.write(chunk)
            saved.append((fn, os.path.getsize(dest)))
        if not saved:
            self._write(400, b"No file received")
            return
        listing = "".join(
            f"<li class='ok'>{html.escape(n)} ({s:,} bytes)</li>" for n, s in saved
        )
        body = (
            "<!doctype html><html><head><meta charset='utf-8'><title>Done</title></head>"
            "<body style='background:#0A0F1A;color:#E0F9FF;font-family:system-ui;"
            "display:flex;align-items:center;justify-content:center;min-height:100vh'>"
            f"<div style='background:#162434;padding:30px 40px;border-radius:14px;"
            f"border:1px solid #39FFB0'><h2 class='ok'>Uploaded OK</h2><ul>{listing}</ul>"
            "<p>You can close this tab now.</p></div></body></html>"
        ).encode()
        self._write(200, body)

    def log_message(self, *args):  # keep console quiet
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8090"))
    srv = HTTPServer(("0.0.0.0", port), Handler)
    print(f"upload server listening on 0.0.0.0:{port}", flush=True)
    srv.serve_forever()
