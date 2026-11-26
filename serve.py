"""Static file server + STL export endpoint.

GET  /*           -> serves files from this directory
POST /export?name=X -> shows a native Save-As dialog, writes body to the
                       chosen path, responds JSON {"saved": path} | {"cancelled": true}
"""
import http.server
import json
import os
import urllib.parse

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def ask_save_path(suggested):
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.asksaveasfilename(
        defaultextension=".stl",
        initialfile=suggested,
        filetypes=[("STL", "*.stl"), ("Alle Dateien", "*.*")],
    )
    root.destroy()
    return path


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, obj):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/export":
            self.send_error(404)
            return
        name = urllib.parse.parse_qs(parsed.query).get("name", ["model"])[0]
        name = "".join(c for c in name if c not in '<>:"/\\|?*').strip() or "model"
        data = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        path = ask_save_path(name + ".stl")
        if not path:
            self._json({"cancelled": True})
            return
        with open(path, "wb") as f:
            f.write(data)
        self._json({"saved": path})

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("localhost", 8000), Handler).serve_forever()
