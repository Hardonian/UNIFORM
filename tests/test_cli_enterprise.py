import json

import pytest

from uniform_lab.cli import main


def test_cli_doctor(capsys) -> None:
    code = main(["doctor"])
    assert code == 0
    captured = capsys.readouterr()
    assert "UNIFORM Lab System Diagnostics" in captured.out
    assert "Core Status: READY" in captured.out


def test_cli_version(capsys) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "uniform 1.0.0rc1" in capsys.readouterr().out


def test_cli_expected_error_is_concise(capsys) -> None:
    assert main(["validate-game", "does-not-exist.json"]) == 2
    captured = capsys.readouterr()
    assert "uniform: error:" in captured.err
    assert "Traceback" not in captured.err


def test_cli_export_lean(tmp_path, capsys) -> None:
    profile_file = tmp_path / "profile.json"
    profile_file.write_text(json.dumps([["0"]]), encoding="utf-8")
    out_file = tmp_path / "cert.lean"
    code = main(
        [
            "export-lean",
            "examples/one_player_zero.json",
            str(profile_file),
            "--output",
            str(out_file),
        ]
    )
    assert code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "theorem certificate_regret_bound :" in content


def test_cli_proof_check(tmp_path, capsys) -> None:
    farkas_file = tmp_path / "farkas.json"
    farkas_file.write_text(
        json.dumps({"matrix": [["1"], ["-1"]], "bounds": ["1", "-2"], "multipliers": ["1", "1"]}),
        encoding="utf-8",
    )

    code = main(["proof-check", str(farkas_file), "--type", "farkas"])
    assert code == 0
    captured = capsys.readouterr()
    assert '"valid": true' in captured.out


def test_cli_validate_game(capsys) -> None:
    code = main(["validate-game", "examples/one_player_zero.json"])
    assert code == 0
    captured = capsys.readouterr()
    assert '"valid": true' in captured.out


def test_cli_periodic(capsys) -> None:
    code = main(
        [
            "periodic",
            "examples/one_player_zero.json",
            "examples/profiles/one_player_zero_profile.json",
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert '"maximum_regret": "0"' in captured.out


def test_cli_algebraic_periodic(capsys) -> None:
    code = main(
        [
            "algebraic-periodic",
            "examples/solan_vieille_2002.json",
            "examples/profiles/solan_vieille_period2_exact_algebraic.json",
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert '"exact_equilibrium_in_scope": true' in captured.out


def test_cli_grid(capsys) -> None:
    code = main(["grid", "examples/one_player_zero.json", "--denominator", "2", "--period", "1"])
    assert code == 0
    captured = capsys.readouterr()
    assert '"maximum_regret": "0"' in captured.out


def test_cli_horizon(capsys) -> None:
    code = main(
        [
            "horizon",
            "examples/one_player_zero.json",
            "examples/profiles/one_player_zero_profile.json",
            "3",
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert '"horizon": 3' in captured.out


def test_cli_smt(tmp_path, capsys) -> None:
    out = tmp_path / "test.smt2"
    code = main(["smt", "examples/one_player_zero.json", "--period", "1", "--output", str(out)])
    assert code == 0
    assert out.exists()


def test_cli_path_check(capsys) -> None:
    code = main(
        ["path-check", "examples/one_player_zero.json", "examples/paths/one_player_continuous.json"]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert '"structurally_valid": true' in captured.out


def test_cli_aps_polytopes(capsys) -> None:
    code = main(
        [
            "aps-polytopes",
            "examples/one_player_zero.json",
            "examples/aps/one_player_seed.json",
            "--steps",
            "1",
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert '"iterations": 1' in captured.out


def test_cli_stochastic(capsys) -> None:
    code = main(
        [
            "stochastic",
            "examples/stochastic/one_state_control.json",
            "examples/stochastic/one_state_half_profile.json",
            "--horizon",
            "2",
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert '"schema": "uniform.stochastic-certificate/v1"' in captured.out


def test_cli_stochastic_smt(tmp_path, capsys) -> None:
    out = tmp_path / "stoch.smt2"
    code = main(
        [
            "stochastic-smt",
            "examples/stochastic/one_state_control.json",
            "--output",
            str(out),
        ]
    )
    assert code == 0
    assert out.exists()


def test_cli_verify_screen(capsys) -> None:
    code = main(["verify-screen", "rust-scanner/benchmark_seed7.json"])
    assert code == 0
    captured = capsys.readouterr()
    assert '"verified_candidates": 3' in captured.out


def test_cli_check_model(tmp_path, capsys) -> None:
    model_file = tmp_path / "model.txt"
    model_file.write_text("sat\n(define-fun q_0_0 () Real 0)", encoding="utf-8")
    code = main(["check-model", "examples/one_player_zero.json", str(model_file), "--period", "1"])
    assert code == 0
    captured = capsys.readouterr()
    assert '"independently_valid": true' in captured.out


def test_cli_environment(capsys) -> None:
    code = main(["environment"])
    assert code == 0
    captured = capsys.readouterr()
    assert '"platform":' in captured.out


def test_cli_solve(tmp_path, capsys) -> None:
    query = tmp_path / "sat.smt2"
    query.write_text("(check-sat)\n", encoding="utf-8")
    code = main(["solve", str(query), "--solver", "z3", "--timeout", "5"])
    assert code == 0
    captured = capsys.readouterr()
    assert '"status": "sat"' in captured.out


def test_cli_solve_campaign(tmp_path, capsys) -> None:
    out_dir = tmp_path / "camp"
    code = main(
        [
            "solve-campaign",
            "examples/one_player_zero.json",
            "--period",
            "1",
            "--solvers",
            "z3",
            "--timeout",
            "5",
            "--output-dir",
            str(out_dir),
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert '"schema": "uniform.solver-campaign/v1"' in captured.out


def test_cli_stochastic_solve_campaign(tmp_path, capsys) -> None:
    out_dir = tmp_path / "stoch_camp"
    code = main(
        [
            "stochastic-solve-campaign",
            "examples/stochastic/one_state_control.json",
            "--solvers",
            "z3",
            "--timeout",
            "5",
            "--output-dir",
            str(out_dir),
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert '"schema": "uniform.solver-campaign/v1"' in captured.out


def test_cli_stochastic_check_model(tmp_path, capsys) -> None:
    model_file = tmp_path / "stoch_model.txt"
    model_file.write_text(
        "sat\n(model (define-fun x_0_0_0 () Real 0) (define-fun x_0_0_1 () Real 1)))",
        encoding="utf-8",
    )
    code = main(
        [
            "stochastic-check-model",
            "examples/stochastic/one_state_control.json",
            str(model_file),
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert '"independently_valid": true' in captured.out


def test_cli_bivariate_prune(tmp_path, capsys) -> None:
    out_file = tmp_path / "biv_cert.json"
    code = main(
        [
            "bivariate-prune",
            "examples/adversarial_candidate_46876.json",
            "--max-evaluations",
            "10",
            "--min-width",
            "1/4",
            "--output",
            str(out_file),
        ]
    )
    # Exits with 0 if certified_unsat else 2
    assert code in (0, 2)
    assert out_file.exists()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["schema"] == "uniform.bivariate-exclusion-certificate/v1"
