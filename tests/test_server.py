import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from uniform_lab.server import WorkbenchRequestHandler, _doctor_diagnostics


def test_doctor_diagnostics() -> None:
    diag = _doctor_diagnostics()
    assert "platform" in diag
    assert "python" in diag
    assert "lake" in diag
    assert diag["schemas_verified"] >= 10
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
            assert data["schema"] == "uniform.algebraic-elimination/v1"
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

    finally:
        server.shutdown()
        server.server_close()

