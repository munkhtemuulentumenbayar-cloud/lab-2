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
        IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif")
        files = sorted(os.listdir(DIR))
        cards = []
        # feature the newest "matched cinematic style" outputs first
        def rank(name):
            n = name.lower()
            if "cinematic" in n:
                return 0
            if "glacial-transparent" in n:
                return 1
            if n.startswith("preview"):
                return 2
            return 3
        files.sort(key=lambda n: (rank(n), n))
        for name in files:
            fp = os.path.join(DIR, name)
            if not os.path.isfile(fp):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext not in IMG_EXT:
                continue
            size = human(os.path.getsize(fp))
            q = urllib.parse.quote(name)
            badge = ""
            if "cinematic" in name.lower():
                badge = "<span class='badge'>NEW · matched style</span>"
            elif "glacial-transparent" in name.lower():
                badge = "<span class='badge'>no background</span>"
            cards.append(
                f"<figure class='card'>"
                f"<a href='/view/{q}' target='_blank'>"
                f"<img loading='lazy' src='/view/{q}' alt='{name}'></a>"
                f"<figcaption>{badge}<br>{name}<br>"
                f"<span class='size'>{size}</span> · "
                f"<a href='/download/{q}'>Download</a></figcaption>"
                f"</figure>"
            )
        html = f"""<!doctype html><html><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Arctic Lens — rendered previews</title><style>
body{{font-family:system-ui,Segoe UI,sans-serif;background:#0a0f1a;color:#dfefff;
 margin:0;padding:32px}}
h1{{color:#7de1ff;font-weight:600;font-size:22px}}
.sub{{color:#8fb0cc;margin-top:4px;font-size:13px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));
 gap:22px;margin-top:22px}}
.card{{margin:0;background:#0e1524;border:1px solid #16233a;border-radius:10px;
 overflow:hidden}}
.card img{{width:100%;height:auto;display:block;background:
 repeating-conic-gradient(#1a2334 0% 25%, #101827 0% 50%) 50%/24px 24px}}
.card figcaption{{padding:10px 12px;font-size:13px;color:#cfE5ff;line-height:1.5}}
.size{{color:#7d93ae}}
.badge{{display:inline-block;background:#0f3d2e;color:#39ffb0;border:1px solid #1e6b4a;
 border-radius:999px;padding:1px 9px;font-size:11px;font-weight:600;
 margin-bottom:4px;letter-spacing:.4px}}
a{{color:#39ffb0;text-decoration:none}} a:hover{{text-decoration:underline}}
.hint{{color:#8fb0cc;margin-top:28px;font-size:13px}}
</style></head><body>
<h1>Arctic Lens — rendered previews</h1>
<div class='sub'>Click any image to open it full size in a new tab;
 use <b>Download</b> to save the PNG to your computer.</div>
<div class='grid'>{''.join(cards)}</div>
<div class='hint'>Tip: a PNG with a transparent background shows on a checkerboard
 pattern here; open it full-size and right-click → Save image as… to keep the
 transparency.</div>
</body></html>"""
        self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    srv = http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"serving {DIR} on 0.0.0.0:{port}")
    srv.serve_forever()
