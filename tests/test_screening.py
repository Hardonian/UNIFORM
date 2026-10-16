import json
from pathlib import Path

from uniform_lab.screening import verify_screen_document


def test_checked_in_million_sample_handoff_verifies_exactly() -> None:
    path = Path(__file__).parents[1] / "rust-scanner" / "benchmark_seed7.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    assert document["samples"] == 1_000_000
    games = verify_screen_document(document)
    assert len(games) == 3
    assert all(game.pure_instant_equilibria() == () for game in games)
