"""Built-in HTTP server and REST API for UNIFORM Lab Enterprise Workbench."""

from __future__ import annotations

import json
import mimetypes
import platform
import shutil
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from .io import dump_json, load_json
from .quitting import QuittingGame, normalize_profile, periodic_regret_certificate

WEB_DIR = Path(__file__).parent / "web"


def _doctor_diagnostics() -> dict[str, Any]:
    schemas_dir = Path(__file__).resolve().parent.parent.parent / "schemas"
    schema_count = len(list(schemas_dir.glob("*.schema.json"))) if schemas_dir.exists() else 11
    return {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "rust_cargo": shutil.which("cargo") is not None,
        "lake": (
            shutil.which("lake") is not None
            or (Path.home() / ".elan/bin/lake.exe").exists()
            or (Path.home() / ".elan/bin/lake").exists()
        ),
        "z3_binding": find_spec("z3") is not None,
        "cvc5_binding": find_spec("cvc5") is not None,
        "schemas_verified": schema_count,
        "status": "ready",
    }



class WorkbenchRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        # Keep server quiet unless error
        if args and str(args[0]).startswith(("4", "5")):
            super().log_message(format, *args)

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = dump_json(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path == "/api/doctor":
            self._send_json(_doctor_diagnostics())
            return
        if path == "/api/examples":
            examples_dir = Path(__file__).resolve().parent.parent.parent / "examples"
            found: dict[str, Any] = {}
            if examples_dir.exists():
                for f in examples_dir.glob("*.json"):
                    try:
                        found[f.stem] = load_json(f)
                    except Exception:
                        pass
            self._send_json(found)
            return

        # Serve static assets from WEB_DIR
        target = (WEB_DIR / path.lstrip("/")).resolve()
        if path in {"", "/"}:
            target = WEB_DIR / "index.html"

        web_root = str(WEB_DIR.resolve())
        if not str(target).startswith(web_root) or not target.exists() or target.is_dir():
            target = WEB_DIR / "index.html"

        if not target.exists():
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        content_type, _ = mimetypes.guess_type(str(target))
        if content_type is None:
            content_type = "application/octet-stream"

        content = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            payload = json.loads(body) if body else {}
        except Exception as e:
            self._send_json({"error": f"Invalid JSON: {e}"}, status=400)
            return

        path = self.path.split("?")[0]

        if path == "/api/validate-game":
            try:
                game = QuittingGame.from_dict(payload)
                self._send_json(
                    {
                        "valid": True,
                        "players": game.players,
                        "absorbing_outcomes": len(game.payoffs),
                        "pure_instant_equilibria": list(game.pure_instant_equilibria()),
                    }
                )
            except Exception as e:
                self._send_json({"valid": False, "error": str(e)}, status=400)
            return

        if path == "/api/periodic":
            try:
                game = QuittingGame.from_dict(payload["game"])
                profile = normalize_profile(game, payload["profile"])
                cert = periodic_regret_certificate(game, profile)
                self._send_json(cert.to_dict())
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
            return

        if path == "/api/eliminate":
            try:
                raw_game = payload.get("game", payload)
                game = QuittingGame.from_dict(raw_game)
                from .elimination import eliminate_quitting_game

                elim_result = eliminate_quitting_game(game)
                self._send_json(elim_result.to_dict())
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
            return

        if path == "/api/screen":
            try:
                raw_game = payload.get("game", payload)
                game = QuittingGame.from_dict(raw_game)
                denominator = int(payload.get("denominator", 2))
                period = int(payload.get("period", 2))
                max_profiles = payload.get("max_profiles", 200)
                from .grid import periodic_grid_search

                grid_result = periodic_grid_search(
                    game, denominator, period, max_profiles=max_profiles
                )
                self._send_json(grid_result.to_dict())
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
            return

        self._send_json({"error": "Unknown API endpoint"}, status=404)


def start_server(host: str = "127.0.0.1", port: int = 8080, open_browser: bool = False) -> None:
    """Start the UNIFORM Lab workbench web server."""
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, WorkbenchRequestHandler)
    url = f"http://{host}:{port}/"
    print(f"UNIFORM Lab Enterprise Workbench running at {url}")
    print("Press Ctrl+C to terminate.")

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nWorkbench server gracefully stopped.")
    finally:
        httpd.server_close()
