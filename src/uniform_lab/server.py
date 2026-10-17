"""Local HTTP server and bounded REST API for the UNIFORM research workbench."""

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

from .io import dump_json
from .quitting import QuittingGame, normalize_profile, periodic_regret_certificate
from .rational import parse_rational
from .resources import example_names, load_example, schema_names

WEB_DIR = Path(__file__).parent / "web"
MAX_REQUEST_BYTES = 1_048_576
MAX_GRID_PROFILES = 100_000
REQUEST_ERRORS = (KeyError, IndexError, TypeError, ValueError, OverflowError)


def _doctor_diagnostics() -> dict[str, Any]:
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
        "schemas_available": len(schema_names()),
        "status": "ready",
    }



class WorkbenchHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


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
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'",
        )

    def do_OPTIONS(self) -> None:
        self.send_response(405)
        self.send_header("Allow", "GET, POST")
        self._send_security_headers()
        self.end_headers()

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path == "/api/doctor":
            self._send_json(_doctor_diagnostics())
            return
        if path == "/api/examples":
            found = {Path(name).stem: load_example(name) for name in example_names()}
            self._send_json(found)
            return
        if path.startswith("/api/"):
            self._send_json({"error": "Unknown API endpoint"}, status=404)
            return

        # Serve static assets from WEB_DIR
        target = (WEB_DIR / path.lstrip("/")).resolve()
        if path in {"", "/"}:
            target = WEB_DIR / "index.html"

        if not target.is_relative_to(WEB_DIR.resolve()) or not target.exists() or target.is_dir():
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
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            self._send_json({"error": "Content-Length is required"}, status=411)
            return
        try:
            content_length = int(raw_length)
        except ValueError:
            self._send_json({"error": "Invalid Content-Length"}, status=400)
            return
        if content_length < 0 or content_length > MAX_REQUEST_BYTES:
            self._send_json(
                {"error": f"Request body exceeds the {MAX_REQUEST_BYTES}-byte limit"}, status=413
            )
            return
        content_type = self.headers.get_content_type()
        if content_type != "application/json":
            self._send_json({"error": "Content-Type must be application/json"}, status=415)
            return
        try:
            body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(body) if body else {}
        except (UnicodeError, json.JSONDecodeError) as e:
            self._send_json({"error": f"Invalid JSON: {e}"}, status=400)
            return
        if not isinstance(payload, dict):
            self._send_json({"error": "JSON request body must be an object"}, status=400)
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
            except REQUEST_ERRORS as e:
                self._send_json({"valid": False, "error": str(e)}, status=400)
            return

        if path == "/api/periodic":
            try:
                game = QuittingGame.from_dict(payload["game"])
                profile = normalize_profile(game, payload["profile"])
                cert = periodic_regret_certificate(game, profile)
                self._send_json(cert.to_dict())
            except REQUEST_ERRORS as e:
                self._send_json({"error": str(e)}, status=400)
            return

        if path == "/api/eliminate":
            try:
                raw_game = payload.get("game", payload)
                game = QuittingGame.from_dict(raw_game)
                from .elimination import eliminate_quitting_game

                elim_result = eliminate_quitting_game(game)
                self._send_json(elim_result.to_dict())
            except REQUEST_ERRORS as e:
                self._send_json({"error": str(e)}, status=400)
            return

        if path == "/api/screen":
            try:
                raw_game = payload.get("game", payload)
                game = QuittingGame.from_dict(raw_game)
                denominator = int(payload.get("denominator", 2))
                period = int(payload.get("period", 2))
                max_profiles = payload.get("max_profiles", 200)
                if not 1 <= denominator <= 20:
                    raise ValueError("denominator must be between 1 and 20")
                if not 1 <= period <= 8:
                    raise ValueError("period must be between 1 and 8")
                if (
                    isinstance(max_profiles, bool)
                    or not isinstance(max_profiles, int)
                    or not 1 <= max_profiles <= MAX_GRID_PROFILES
                ):
                    raise ValueError(
                        f"max_profiles must be an integer from 1 to {MAX_GRID_PROFILES}"
                    )
                from .grid import periodic_grid_search

                grid_result = periodic_grid_search(
                    game, denominator, period, max_profiles=max_profiles
                )
                self._send_json(grid_result.to_dict())
            except REQUEST_ERRORS as e:
                self._send_json({"error": str(e)}, status=400)
            return

        if path == "/api/bivariate-prune":
            try:
                raw_game = payload.get("game", payload)
                game = QuittingGame.from_dict(raw_game)
                from .bivariate import BivariateBox, RationalInterval, prune_quitting_game

                d_lo = parse_rational(payload.get("domain_lo", "1/100"), field="domain_lo")
                d_hi = parse_rational(payload.get("domain_hi", "99/100"), field="domain_hi")
                min_w = parse_rational(payload.get("min_width", "1/256"), field="min_width")
                max_evals = int(payload.get("max_evaluations", 200))
                domain = BivariateBox(RationalInterval(d_lo, d_hi), RationalInterval(d_lo, d_hi))
                biv_cert = prune_quitting_game(
                    game, domain=domain, max_evaluations=max_evals, min_width=min_w
                )
                self._send_json(biv_cert.to_dict())
            except REQUEST_ERRORS as e:
                self._send_json({"error": str(e)}, status=400)
            return

        self._send_json({"error": "Unknown API endpoint"}, status=404)


def start_server(host: str = "127.0.0.1", port: int = 8080, open_browser: bool = False) -> None:
    """Start the UNIFORM Lab workbench web server."""
    if not 0 <= port <= 65_535:
        raise ValueError("port must be between 0 and 65535")
    server_address = (host, port)
    httpd = WorkbenchHTTPServer(server_address, WorkbenchRequestHandler)
    actual_port = int(httpd.server_address[1])
    url = f"http://{host}:{actual_port}/"
    print(f"UNIFORM Lab research workbench running at {url}")
    if host not in {"127.0.0.1", "localhost", "::1"}:
        print("WARNING: this unauthenticated research API is exposed beyond the loopback host.")
    print("Press Ctrl+C to terminate.")

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nWorkbench server gracefully stopped.")
    finally:
        httpd.server_close()
