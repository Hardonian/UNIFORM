from fractions import Fraction

from uniform_lab.io import load_quitting_game
from uniform_lab.lean_exporter import export_lean_certificate
from uniform_lab.quitting import normalize_profile, periodic_regret_certificate


def test_export_lean_certificate() -> None:
    game = load_quitting_game("examples/one_player_zero.json")
    profile = normalize_profile(game, [[Fraction(0)]])
    cert = periodic_regret_certificate(game, profile)
    code = export_lean_certificate(game, cert, module_name="Uniform.OnePlayerTest")

    assert "module" in code
    assert "import Uniform.Certificate" in code
    assert "namespace OnePlayerTest" in code
    assert "def numPlayers : Nat := 1" in code
    assert "def maximumRegret : ℚ := 0" in code
    assert "theorem certificate_regret_bound :" in code
    assert "decide" in code
