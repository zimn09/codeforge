"""Built-in development server with automatic browser reloads.

The server intentionally uses only the Python standard library.  HTML pages
are served with a tiny polling script injected before ``</body>``.  The script
asks the server for a cheap workspace fingerprint and reloads the page when
files are saved.
"""

from __future__ import annotations

import mimetypes
import os
import threading
import time
import urllib.parse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_VERSION_PATH = "/__codeforge_version__"
_SCRIPT_MARKER = "__codeforge_live_reload__"
_IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
    "venv",
    ".venv",
}

_LIVE_RELOAD_SCRIPT = f"""
<script id="{_SCRIPT_MARKER}">
(() => {{
  let current = null;
  async function check() {{
    try {{
      const response = await fetch("{_VERSION_PATH}", {{cache: "no-store"}});
      const next = await response.text();
      if (current !== null && next !== current) {{
        window.location.reload();
        return;
      }}
      current = next;
    }} catch (error) {{
      /* The server is probably restarting; retry shortly. */
    }}
    window.setTimeout(check, 600);
  }}
  check();
}})();
</script>
"""


class _LiveRequestHandler(SimpleHTTPRequestHandler):
    """Serve files below one root and inject the live-reload snippet."""

    server_version = "CodeForgeLive/1.0"

    def do_GET(self) -> None:  # noqa: N802 (Qt/HTTP API)
        request_path = urllib.parse.unquote(
            urllib.parse.urlparse(self.path).path
        )
        if request_path == _VERSION_PATH:
            self._send_version()
            return

        translated = Path(self.translate_path(self.path))
        if translated.is_dir():
            if not request_path.endswith("/"):
                super().do_GET()
                return
            for index_name in ("index.html", "index.htm", "index.xhtml"):
                index = translated / index_name
                if index.is_file():
                    self._send_html(index)
                    return
        elif translated.is_file() and translated.suffix.lower() in {
            ".html",
            ".htm",
            ".xhtml",
        }:
            self._send_html(translated)
            return

        super().do_GET()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def log_message(self, _format: str, *args) -> None:
        """Silence the default per-request stderr logging."""

    def _send_version(self) -> None:
        owner = getattr(self.server, "owner", None)
        value = owner.version() if owner is not None else "0"
        data = value.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, path: Path) -> None:
        try:
            data = path.read_bytes()
        except OSError:
            self.send_error(404, "File not found")
            return

        text = data.decode("utf-8", errors="replace")
        if _SCRIPT_MARKER not in text:
            lower = text.lower()
            insert_at = lower.rfind("</body>")
            if insert_at < 0:
                insert_at = lower.rfind("</html>")
            if insert_at >= 0:
                text = (
                    text[:insert_at]
                    + _LIVE_RELOAD_SCRIPT
                    + text[insert_at:]
                )
            else:
                text += _LIVE_RELOAD_SCRIPT

        payload = text.encode("utf-8")
        content_type = (
            mimetypes.guess_type(str(path))[0] or "text/html"
        )
        if content_type.startswith("text/") and "charset" not in content_type:
            content_type += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


class LiveServer:
    """A local HTTP server that can be started and stopped from the UI."""

    def __init__(self) -> None:
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._root: Path | None = None
        self._port: int | None = None
        self._lock = threading.Lock()
        self._cached_at = 0.0
        self._cached_version = "0"

    @property
    def running(self) -> bool:
        return self._httpd is not None

    @property
    def root(self) -> Path | None:
        return self._root

    @property
    def port(self) -> int | None:
        return self._port

    @property
    def url(self) -> str:
        if self._port is None:
            return ""
        return f"http://127.0.0.1:{self._port}"

    def start(self, root: Path, preferred_port: int = 5500) -> str:
        """Start the server for *root* and return its base URL."""
        root = Path(root).expanduser().resolve()
        if not root.is_dir():
            raise OSError(f"Live Server folder does not exist: {root}")

        self.stop()
        handler = partial(_LiveRequestHandler, directory=str(root))
        httpd: ThreadingHTTPServer | None = None
        last_error: OSError | None = None
        for port in range(preferred_port, preferred_port + 20):
            try:
                httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
                self._port = port
                break
            except OSError as exc:
                last_error = exc
        if httpd is None:
            detail = f": {last_error}" if last_error else ""
            raise OSError(
                f"No free port in {preferred_port}-{preferred_port + 19}{detail}"
            )

        httpd.daemon_threads = True
        httpd.owner = self  # type: ignore[attr-defined]
        self._root = root
        self._httpd = httpd
        with self._lock:
            self._cached_at = 0.0
            self._cached_version = "0"
        self._thread = threading.Thread(
            target=httpd.serve_forever,
            name="codeforge-live-server",
            daemon=True,
        )
        self._thread.start()
        return self.url

    def stop(self) -> None:
        httpd = self._httpd
        thread = self._thread
        self._httpd = None
        self._thread = None
        self._port = None
        if httpd is not None:
            try:
                httpd.shutdown()
            except OSError:
                pass
            try:
                httpd.server_close()
            except OSError:
                pass
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)
        self._root = None

    def url_for(self, path: Path | None = None) -> str:
        """Return the browser URL for a file below the served root."""
        if self._port is None:
            return ""
        base = self.url + "/"
        if path is None or self._root is None:
            return base
        try:
            relative = Path(path).expanduser().resolve().relative_to(
                self._root
            )
        except (OSError, ValueError):
            return base
        return base + urllib.parse.quote(relative.as_posix())

    def version(self) -> str:
        """Return a cheap fingerprint that changes when workspace files save."""
        if self._root is None:
            return "0"
        now = time.monotonic()
        with self._lock:
            if now - self._cached_at < 0.35:
                return self._cached_version

        latest = 0
        total_size = 0
        count = 0
        for base, directories, files in os.walk(self._root):
            directories[:] = [
                name
                for name in directories
                if name not in _IGNORED_DIRECTORIES
            ]
            for name in files:
                try:
                    stat = (Path(base) / name).stat()
                except OSError:
                    continue
                latest = max(latest, stat.st_mtime_ns)
                total_size += stat.st_size
                count += 1

        value = f"{latest}:{count}:{total_size}"
        with self._lock:
            self._cached_at = now
            self._cached_version = value
        return value
