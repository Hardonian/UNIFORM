import json

from uniform_lab.cli import main


def test_cli_doctor(capsys) -> None:
    code = main(["doctor"])
    assert code == 0
    captured = capsys.readouterr()
    assert "UNIFORM Lab Enterprise System Diagnostics" in captured.out
    assert "Overall System Status: ENTERPRISE READY" in captured.out


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
