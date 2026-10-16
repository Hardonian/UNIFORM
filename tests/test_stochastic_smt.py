from fractions import Fraction
from importlib.util import find_spec
from pathlib import Path

import pytest

from uniform_lab.io import load_stochastic_game
from uniform_lab.smt import parse_solver_model
from uniform_lab.solver import build_stochastic_solver_artifact
from uniform_lab.stochastic_smt import (
    export_discounted_stationary_qfnra,
    independently_check_stochastic_model,
    stationary_profile_from_model,
)

ROOT = Path(__file__).parents[1]


def test_stochastic_export_is_scoped_qfnra() -> None:
    game = load_stochastic_game(ROOT / "examples" / "stochastic" / "one_state_control.json")
    text = export_discounted_stationary_qfnra(game, Fraction(9, 10), Fraction(0))
    assert "(set-logic QF_NRA)" in text
    assert "all unilateral discounted deviations" in text
    assert "UNSAT excludes only the independent stationary profile class" in text
    assert "d_0_1_0" in text


def test_rational_stochastic_profile_model_extraction() -> None:
    game = load_stochastic_game(ROOT / "examples" / "stochastic" / "one_state_control.json")
    model = parse_solver_model(
        "sat\n(model (define-fun x_0_0_0 () Real 0) "
        "(define-fun x_0_0_1 () Real 1)))"
    )
    profile = stationary_profile_from_model(game, model)
    assert profile == (((Fraction(0), Fraction(1)),),)


def test_two_state_transition_sensitive_witness() -> None:
    game = load_stochastic_game(
        ROOT / "examples" / "stochastic" / "two_state_control.json"
    )
    model_text = (
        "sat\n(model "
        "(define-fun x_0_0_0 () Real 0) "
        "(define-fun x_0_0_1 () Real 1) "
        "(define-fun x_1_0_0 () Real 1) "
        "(define-fun x_1_0_1 () Real 0)))"
    )
    _, profile, valid = independently_check_stochastic_model(
        game, Fraction(1, 2), Fraction(0), model_text
    )
    assert valid
    assert game.discounted_values(profile, Fraction(1, 2)) == (
        (Fraction(1, 2),),
        (Fraction(1),),
    )
    text = export_discounted_stationary_qfnra(game, Fraction(1, 2), Fraction(0))
    assert "v_0_1" in text
    assert "d_0_3_1" in text


@pytest.mark.parametrize("solver", ["z3", "cvc5"])
def test_stochastic_solver_witness_rechecks_exactly(solver: str, tmp_path: Path) -> None:
    if find_spec(solver) is None:
        pytest.skip(f"optional {solver} binding is not installed")
    game = load_stochastic_game(ROOT / "examples" / "stochastic" / "one_state_control.json")
    query = tmp_path / "stochastic.smt2"
    query.write_text(
        export_discounted_stationary_qfnra(game, Fraction(9, 10), Fraction(0)),
        encoding="utf-8",
    )
    artifact = build_stochastic_solver_artifact(
        query,
        solver,
        game=game,
        beta=Fraction(9, 10),
        epsilon=Fraction(0),
    )
    assert artifact.run.status == "sat"
    assert artifact.independent_verification == "passed"
    assert artifact.parameters["beta"] == "9/10"
    _, profile, valid = independently_check_stochastic_model(
        game, Fraction(9, 10), Fraction(0), artifact.run.stdout
    )
    assert valid
    assert game.discounted_stationary_regret(profile, Fraction(9, 10)) == (
        (Fraction(0),),
    )
