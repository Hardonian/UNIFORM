import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError

from uniform_lab.server import WorkbenchRequestHandler, _doctor_diagnostics


def test_doctor_diagnostics() -> None:
    diag = _doctor_diagnostics()
    assert "platform" in diag
    assert "python" in diag
    assert "lake" in diag
    assert diag["schemas_available"] >= 20
    assert diag["status"] == "ready"


def test_web_directory_exists() -> None:
    web_dir = Path(__file__).resolve().parent.parent / "src" / "uniform_lab" / "web"
    assert (web_dir / "index.html").exists()
    assert (web_dir / "style.css").exists()
    assert (web_dir / "app.js").exists()


def test_server_live_endpoints() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), WorkbenchRequestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"

    try:
        # Test GET /api/doctor
        with urllib.request.urlopen(f"{base_url}/api/doctor") as resp:
            data = json.loads(resp.read().decode())
            assert data["status"] == "ready"
            assert resp.headers["X-Content-Type-Options"] == "nosniff"
            assert resp.headers["Access-Control-Allow-Origin"] is None

        # Test GET /
        with urllib.request.urlopen(f"{base_url}/") as resp:
            content = resp.read().decode()
            assert "<!DOCTYPE html>" in content

        # Test POST /api/validate-game
        game_payload = {
            "schema": "uniform.quitting-game/v1",
            "players": 2,
            "continuation": [0, 0],
            "payoffs": {"1": [1, -1], "2": [-1, 1], "3": [-2, -2]},
        }
        req = urllib.request.Request(
            f"{base_url}/api/validate-game",
            data=json.dumps(game_payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            assert data["valid"] is True
            assert data["players"] == 2

        # Test POST /api/eliminate
        req_elim = urllib.request.Request(
            f"{base_url}/api/eliminate",
            data=json.dumps({"game": game_payload}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_elim) as resp:
            data = json.loads(resp.read().decode())
            assert data["schema"] in {
                "uniform.algebraic-elimination/v1",
                "uniform.algebraic-elimination/v2",
            }
            assert data["players"] == 2

        # Test POST /api/periodic
        req_periodic = urllib.request.Request(
            f"{base_url}/api/periodic",
            data=json.dumps({
                "game": game_payload,
                "profile": [[0, 0]],
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_periodic) as resp:
            data = json.loads(resp.read().decode())
            assert data["schema"] == "uniform.periodic-regret-certificate/v1"
            assert "maximum_regret" in data

        # Test GET /api/examples
        with urllib.request.urlopen(f"{base_url}/api/examples") as resp:
            data = json.loads(resp.read().decode())
            assert isinstance(data, dict)
            assert len(data) > 0

        # Test GET static files
        with urllib.request.urlopen(f"{base_url}/app.js") as resp:
            assert resp.status == 200
            assert "javascript" in resp.headers["Content-Type"]
        with urllib.request.urlopen(f"{base_url}/style.css") as resp:
            assert resp.status == 200
            assert "text/css" in resp.headers["Content-Type"]


        # Test POST /api/screen
        req_screen = urllib.request.Request(
            f"{base_url}/api/screen",
            data=json.dumps({
                "game": game_payload,
                "denominator": 2,
                "period": 1,
                "max_profiles": 10,
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_screen) as resp:
            data = json.loads(resp.read().decode())
            assert data["schema"] == "uniform.periodic-grid-search/v1"


    finally:
        server.shutdown()
        server.server_close()



def test_server_rejects_unsafe_or_unbounded_requests() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), WorkbenchRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        wrong_type = urllib.request.Request(
            f"{base_url}/api/validate-game", data=b"{}", headers={"Content-Type": "text/plain"}
        )
        try:
            urllib.request.urlopen(wrong_type)
        except HTTPError as exc:
            assert exc.code == 415

        too_large = urllib.request.Request(
            f"{base_url}/api/validate-game",
            data=b"{}",
            headers={"Content-Type": "application/json", "Content-Length": "1048577"},
        )
        try:
            urllib.request.urlopen(too_large)
        except HTTPError as exc:
            assert exc.code == 413

        invalid_grid = urllib.request.Request(
            f"{base_url}/api/screen",
            data=json.dumps({"denominator": 21}).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(invalid_grid)
        except HTTPError as exc:
            assert exc.code == 400
    finally:
        server.shutdown()
        server.server_close()
