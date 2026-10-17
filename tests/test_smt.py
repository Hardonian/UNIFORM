from fractions import Fraction
from importlib.util import find_spec
from pathlib import Path

import pytest

import uniform_lab.solver as solver_module
from uniform_lab.quitting import QuittingGame, periodic_regret_certificate
from uniform_lab.smt import (
    evaluate_rational,
    export_periodic_qfnra,
    parse_solver_model,
    profile_from_model,
)
from uniform_lab.solver import build_solver_artifact, persist_solver_artifact, run_solver


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


def test_solver_artifact_hash_and_independent_check(tmp_path: Path) -> None:
    if find_spec("z3") is None:
        pytest.skip("optional z3 binding is not installed")
    game = QuittingGame(1, {1: (Fraction(0),)}, (Fraction(0),))
    query = tmp_path / "query.smt2"
    query.write_text(export_periodic_qfnra(game, 1, Fraction(0)), encoding="utf-8")
    artifact = build_solver_artifact(query, "z3", game=game, period=1, epsilon=Fraction(0))
    assert artifact.run.status == "sat"
    assert artifact.independent_verification == "passed"
    assert artifact.game_sha256 is not None and len(artifact.game_sha256) == 64
    path = persist_solver_artifact(artifact, tmp_path / "artifact")
    assert path.exists()
    assert len(artifact.query_sha256) == 64


def test_z3_native_unsat_proof_is_retained_when_requested(tmp_path: Path) -> None:
    if find_spec("z3") is None:
        pytest.skip("optional z3 binding is not installed")
    query = tmp_path / "unsat.smt2"
    query.write_text("(set-logic QF_LRA)\n(assert false)\n(check-sat)\n", encoding="utf-8")
    run = run_solver(query, "z3", produce_proof=True)
    assert run.status == "unsat"
    assert run.proof


def test_python_binding_has_a_hard_parent_timeout(monkeypatch, tmp_path: Path) -> None:
    query = tmp_path / "query.smt2"
    query.write_text("(check-sat)\n", encoding="utf-8")
    monkeypatch.setattr(solver_module.shutil, "which", lambda _name: None)

    def expire(*args, **kwargs):
        raise solver_module.subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(solver_module.subprocess, "run", expire)
    run = run_solver(query, "z3", timeout=Fraction(1, 100))
    assert run.status == "timeout"
    assert run.timed_out is True
    assert run.returncode == 124


def test_direct_python_binding_direct_z3(tmp_path: Path) -> None:
    if find_spec("z3") is None:
        pytest.skip("optional z3 binding is not installed")
    from uniform_lab.solver import _run_python_binding_direct

    query = tmp_path / "sat.smt2"
    query.write_text("(check-sat)\n", encoding="utf-8")
    run = _run_python_binding_direct(query, "z3", timeout=5.0, produce_proof=False)
    assert run.status == "sat"


def test_direct_python_binding_direct_cvc5(tmp_path: Path) -> None:
    if find_spec("cvc5") is None:
        pytest.skip("optional cvc5 binding is not installed")
    from uniform_lab.solver import _run_python_binding_direct

    query = tmp_path / "sat_cvc5.smt2"
    query.write_text("(check-sat)\n", encoding="utf-8")
    run = _run_python_binding_direct(query, "cvc5", timeout=5.0, produce_proof=False)
    assert run.status == "sat"



def test_solver_hard_timeout_enforced(tmp_path: Path) -> None:
    if find_spec("z3") is None:
        pytest.skip("optional z3 binding is not installed")
    query = tmp_path / "timeout_query.smt2"
    # An unsolvable nonlinear query or simple check with an ultra-short timeout
    query.write_text(
        "(set-logic QF_NRA)\n"
        "(declare-fun x () Real)\n"
        "(assert (= (+ (* x x x x x) (* x x x) 1.0) 0.0))\n"
        "(check-sat)\n",
        encoding="utf-8",
    )
    run = run_solver(query, "z3", timeout=0.001)
    assert run.timed_out is True
    assert run.status == "timeout"
    assert run.elapsed_seconds < 4.0


