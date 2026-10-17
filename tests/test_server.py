from pathlib import Path

from uniform_lab.server import _doctor_diagnostics


def test_doctor_diagnostics() -> None:
    diag = _doctor_diagnostics()
    assert "platform" in diag
    assert "python" in diag
    assert "lake" in diag
    assert diag["schemas_verified"] == 10
    assert diag["status"] == "ready"


def test_web_directory_exists() -> None:
    web_dir = Path(__file__).resolve().parent.parent / "src" / "uniform_lab" / "web"
    assert (web_dir / "index.html").exists()
    assert (web_dir / "style.css").exists()
    assert (web_dir / "app.js").exists()
