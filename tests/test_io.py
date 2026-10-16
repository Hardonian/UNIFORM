from fractions import Fraction
from pathlib import Path

from uniform_lab.io import (
    load_absorption_path,
    load_quitting_game,
    load_stationary_profile,
    load_stochastic_game,
)

ROOT = Path(__file__).parents[1]


def test_absorption_path_json_round_trip_into_checker() -> None:
    game = load_quitting_game(ROOT / "examples" / "one_player_zero.json")
    path = load_absorption_path(game, ROOT / "examples" / "paths" / "one_player_continuous.json")
    assert path.check().valid
    assert path.sequential_epsilon_check().valid


def test_stochastic_json_loaders() -> None:
    game = load_stochastic_game(ROOT / "examples" / "stochastic" / "one_state_control.json")
    profile = load_stationary_profile(
        game, ROOT / "examples" / "stochastic" / "one_state_half_profile.json"
    )
    assert game.discounted_values(profile, Fraction(9, 10)) == ((Fraction(1),),)
