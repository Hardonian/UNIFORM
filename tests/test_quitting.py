from fractions import Fraction
from pathlib import Path

from uniform_lab.io import load_quitting_game
from uniform_lab.quitting import (
    QuittingGame,
    finite_horizon_certificate,
    normalize_profile,
    periodic_regret_certificate,
    periodic_values,
)

ROOT = Path(__file__).parents[1]


def test_never_absorbing_uses_continuation_payoff() -> None:
    game = QuittingGame(1, {1: (Fraction(7),)}, (Fraction(3),))
    profile = normalize_profile(game, [[0]])
    assert periodic_values(game, profile) == ((Fraction(3),),)


def test_single_player_deviation_and_horizon_are_exact() -> None:
    game = QuittingGame(1, {1: (Fraction(7),)}, (Fraction(3),))
    profile = normalize_profile(game, [["1/2"]])
    certificate = periodic_regret_certificate(game, profile)
    assert certificate.values == ((Fraction(7),),)
    assert certificate.maximum_regret == 0
    finite = finite_horizon_certificate(game, profile, 2)
    assert finite.value == (Fraction(6),)
    assert finite.best_deviation_value == (Fraction(7),)
    assert finite.regret == (Fraction(1),)


def test_published_payoff_table_and_period_two_candidate() -> None:
    game = load_quitting_game(ROOT / "examples" / "solan_vieille_2002.json")
    assert game.payoffs[1] == (Fraction(1), Fraction(4), Fraction(0), Fraction(0))
    assert game.payoffs[15] == (Fraction(-1),) * 4
    assert game.pure_instant_equilibria() == ()
    data = __import__("json").loads(
        (ROOT / "examples" / "profiles" / "solan_vieille_period2_rational_approx.json").read_text()
    )
    profile = normalize_profile(game, data["profile"])
    certificate = periodic_regret_certificate(game, profile)
    assert certificate.maximum_regret < Fraction(1, 10**14)


def test_all_periodic_start_phases_are_checked() -> None:
    game = QuittingGame(1, {1: (Fraction(1),)}, (Fraction(0),))
    profile = normalize_profile(game, [[0], [1]])
    certificate = periodic_regret_certificate(game, profile)
    assert certificate.period == 2
    assert len(certificate.regrets) == 2
