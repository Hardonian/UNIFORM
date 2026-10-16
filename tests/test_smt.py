from fractions import Fraction
from importlib.util import find_spec
from pathlib import Path

import pytest

from uniform_lab.quitting import QuittingGame, periodic_regret_certificate
from uniform_lab.smt import (
    evaluate_rational,
    export_periodic_qfnra,
    parse_solver_model,
    profile_from_model,
)
from uniform_lab.solver import run_solver


def test_export_is_honestly_scoped_and_qfnra() -> None:
    game = QuittingGame(1, {1: (Fraction(1),)}, (Fraction(0),))
    text = export_periodic_qfnra(game, 2, Fraction(1, 10))
    assert "(set-logic QF_NRA)" in text
    assert "UNSAT excludes only this bounded strategy class" in text
    assert "d_0_3_1" in text


def test_model_parser_handles_solver_rational_syntax() -> None:
    model = parse_solver_model(
        "sat\n(model (define-fun q_0_0 () Real (/ 1.0 2.0)) "
        "(define-fun q_0_1 () Real (- (/ 3 4)))))"
    )
    assert model.status == "sat"
    assert model.rationals == {"q_0_0": Fraction(1, 2), "q_0_1": Fraction(-3, 4)}
    assert evaluate_rational(["/", "7", "9"]) == Fraction(7, 9)


def test_model_parser_handles_z3_standalone_definitions() -> None:
    model = parse_solver_model("sat\n(define-fun q_0_0 () Real (/ 1.0 2.0))")
    assert model.rationals["q_0_0"] == Fraction(1, 2)


@pytest.mark.parametrize("solver", ["z3", "cvc5"])
def test_optional_solver_binding_round_trip(solver: str, tmp_path: Path) -> None:
    if find_spec(solver) is None:
        pytest.skip(f"optional {solver} binding is not installed")
    game = QuittingGame(1, {1: (Fraction(0),)}, (Fraction(0),))
    path = tmp_path / "query.smt2"
    path.write_text(export_periodic_qfnra(game, 1, Fraction(0)), encoding="utf-8")
    run = run_solver(path, solver)
    assert run.returncode == 0
    model = parse_solver_model(run.stdout)
    profile = profile_from_model(game, 1, model)
    assert periodic_regret_certificate(game, profile).maximum_regret == 0
