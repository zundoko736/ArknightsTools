import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import search


ROOT = Path(__file__).resolve().parent
EXPORTED_DIR = ROOT / "exported"
WEB_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/search.js": ("search.js", "text/javascript; charset=utf-8"),
}


class WebAppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        request = urlsplit(self.path)
        if request.path in WEB_FILES:
            self._send_file(*WEB_FILES[request.path])
        elif request.path == "/api/status":
            self._send_status()
        elif request.path == "/api/search":
            self._search(request.query)
        else:
            self.send_error(404)

    def _send_file(self, name, content_type):
        content = (ROOT / name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_json(self, payload, status=200):
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_status(self):
        if not EXPORTED_DIR.is_dir():
            self._send_json({"ok": False, "error": "exported directory was not found"}, 500)
            return

        file_count = sum(
            1
            for path in EXPORTED_DIR.rglob("*")
            if path.is_file() and path.suffix.lower() == ".txt"
        )
        self._send_json({"ok": True, "file_count": file_count})

    def _search(self, query):
        parameters = parse_qs(query, keep_blank_values=True)
        text = parameters.get("text", [""])[0] or None
        by_text = parameters.get("by", [""])[0] or None
        if text is None and by_text is None:
            self._send_json({"error": "provide text, by, or both"}, 400)
            return

        try:
            matches = list(search.iter_matches(EXPORTED_DIR, text, by_text))
        except (OSError, UnicodeError) as error:
            self._send_json({"error": str(error)}, 500)
            return
        self._send_json({"matches": matches})


def main():
    if not EXPORTED_DIR.is_dir():
        raise FileNotFoundError(f"Search directory does not exist: {EXPORTED_DIR}")

    server = ThreadingHTTPServer(("127.0.0.1", 8000), WebAppHandler)
    print("Story search is available at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping story search server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
