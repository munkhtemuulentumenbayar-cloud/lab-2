"""
Tiny download server for the rendered files in renders/.
Run:  .venv/bin/python download_server.py  (binds 0.0.0.0:8080)
Lists every file with a "Download" link (forced attachment) and a "View" link.
"""
import os
import http.server
import urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.join(BASE, "renders")

CTYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".txt": "text/plain; charset=utf-8",
    ".py": "text/plain; charset=utf-8",
    ".json": "application/json",
}


def human(n):
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0
    return f"{n:.1f} MB"


def safe_file(name):
    """Resolve a requested name strictly inside DIR (no traversal)."""
    path = os.path.realpath(os.path.join(DIR, name))
    if not path.startswith(os.path.realpath(DIR) + os.sep):
        return None
    return path if os.path.isfile(path) else None


class Handler(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(url.path)
        if path in ("/", "/index.html"):
            self.index()
        elif path.startswith("/download/"):
            self.serve(path[len("/download/"):], attach=True)
        elif path.startswith("/view/"):
            self.serve(path[len("/view/"):], attach=False)
        else:
            self._send(404, b"not found", "text/plain")

    def serve(self, name, attach):
        fp = safe_file(name)
        if fp is None:
            self._send(404, b"file not found", "text/plain")
            return
        with open(fp, "rb") as f:
            data = f.read()
        ext = os.path.splitext(fp)[1].lower()
        ctype = CTYPES.get(ext, "application/octet-stream")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if attach:
            self.send_header("Content-Disposition",
                             f'attachment; filename="{os.path.basename(fp)}"')
        self.end_headers()
        self.wfile.write(data)

    def index(self):
        files = sorted(os.listdir(DIR))
        rows = []
        for name in files:
            fp = os.path.join(DIR, name)
            if not os.path.isfile(fp):
                continue
            size = human(os.path.getsize(fp))
            q = urllib.parse.quote(name)
            rows.append(
                f"<tr><td>{name}</td><td>{size}</td>"
                f"<td><a href='/download/{q}'>Download</a></td>"
                f"<td><a href='/view/{q}' target='_blank'>View</a></td></tr>"
            )
        html = f"""<!doctype html><html><head><meta charset='utf-8'>
<title>Arctic Lens renders</title><style>
body{{font-family:system-ui,Segoe UI,sans-serif;background:#0a0f1a;color:#dfefff;
 margin:0;padding:40px}} h1{{color:#7de1ff;font-weight:600}}
 table{{border-collapse:collapse;width:100%;max-width:900px;margin-top:16px}}
 td,th{{padding:10px 14px;border-bottom:1px solid #16233a;text-align:left;font-size:14px}}
 a{{color:#39ffb0;text-decoration:none}} a:hover{{text-decoration:underline}}
 th{{color:#8fb0cc;font-weight:600}}
 .hint{{color:#8fb0cc;margin-top:24px;font-size:13px}}
</style></head><body>
<h1>Arctic Lens — rendered files</h1>
<table><tr><th>File</th><th>Size</th><th></th><th></th></tr>
{''.join(rows)}
</table>
<div class='hint'>“Download” saves the file to your computer. “View” opens it in a new tab
 (right-click → Save image as… on a PNG also works).</div>
</body></html>"""
        self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    srv = http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"serving {DIR} on 0.0.0.0:{port}")
    srv.serve_forever()
