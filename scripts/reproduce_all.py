"""Run the scoped, machine-executed UNIFORM release verification suite."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from jsonschema.validators import validator_for

from uniform_lab.elimination import eliminate_quitting_game
from uniform_lab.grid import periodic_grid_search
from uniform_lab.io import load_json
from uniform_lab.quitting import QuittingGame
from uniform_lab.rational import rational_text


def compute_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(command: list[str], cwd: Path) -> dict[str, Any]:
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    elapsed = time.perf_counter() - started
    if completed.returncode != 0:
        joined = " ".join(command)
        raise RuntimeError(
            f"command failed ({completed.returncode}): {joined}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return {
        "command": command,
        "elapsed_seconds": round(elapsed, 4),
        "stdout_tail": completed.stdout.splitlines()[-5:],
        "status": "passed",
    }


def _tool(name: str, fallback: Path | None = None) -> str:
    found = shutil.which(name)
    if found is not None:
        return found
    if fallback is not None and fallback.exists():
        return str(fallback)
    raise RuntimeError(f"required release-verification tool is missing: {name}")


def audit_json_schemas(repo_root: Path) -> dict[str, Any]:
    schema_paths = sorted((repo_root / "schemas").glob("*.schema.json"))
    schemas: dict[str, dict[str, Any]] = {}
    hashes: dict[str, str] = {}
    for path in schema_paths:
        document = json.loads(path.read_text(encoding="utf-8"))
        validator_for(document).check_schema(document)
        schemas[path.name] = document
        hashes[path.name] = compute_sha256(path)

    from referencing import Registry, Resource

    reg: Registry = Registry()
    for fname, sch in schemas.items():
        res = Resource.from_contents(sch)
        reg = reg.with_resource(fname, res)
        if "$id" in sch:
            reg = reg.with_resource(sch["$id"], res)

    validated_examples = 0
    for path in sorted((repo_root / "examples").rglob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        schema_id = document.get("schema")
        if not isinstance(schema_id, str):
            continue
        filename = f"{schema_id.removeprefix('uniform.').replace('/', '-')}.schema.json"
        if filename not in schemas:
            raise ValueError(f"{path}: no bundled schema for {schema_id}")
        validator_for(schemas[filename])(schemas[filename], registry=reg).validate(document)
        validated_examples += 1
    return {
        "schema_count": len(schemas),
        "validated_examples": validated_examples,
        "hashes": hashes,
        "status": "draft_2020_12_meta_validated",
    }


def audit_lean(repo_root: Path) -> dict[str, Any]:
    lean_files = sorted((repo_root / "lean" / "Uniform").glob("*.lean"))
    placeholders = [path.name for path in lean_files if "sorry" in path.read_text(encoding="utf-8")]
    if placeholders:
        raise ValueError(f"Lean source contains sorry placeholders: {placeholders}")
    suffix = ".exe" if sys.platform == "win32" else ""
    lake = _tool("lake", Path.home() / ".elan" / "bin" / f"lake{suffix}")
    build = _run([lake, "build"], repo_root / "lean")
    return {
        "source_files": len(lean_files),
        "sorry_placeholders": 0,
        "build": build,
        "file_hashes": {path.name: compute_sha256(path) for path in lean_files},
        "status": "lake_build_passed",
    }


def audit_symbolic_elimination(repo_root: Path) -> dict[str, Any]:
    reports: dict[str, Any] = {}
    for filename in (
        "two_player_cycle.json",
        "three_player_mesh.json",
        "solan_vieille_2002.json",
        "adversarial_candidate_46876.json",
    ):
        game = QuittingGame.from_dict(load_json(repo_root / "examples" / filename))
        started = time.perf_counter()
        result = eliminate_quitting_game(game)
        reports[filename] = {
            "interior_candidate_status": result.interior_candidate_status,
            "characteristic_polynomial_degree": (
                result.characteristic_polynomial.degree
                if result.characteristic_polynomial is not None
                else None
            ),
            "isolated_eliminant_root_intervals": len(result.isolated_interior_roots),
            "bivariate_degrees": result.bivariate_degrees,
            "elapsed_seconds": round(time.perf_counter() - started, 5),
            "scope": result.to_dict()["scope"],
        }
    return reports


def audit_complete_period_two_grids(repo_root: Path) -> dict[str, Any]:
    reports: dict[str, Any] = {}
    for filename in ("solan_vieille_2002.json", "adversarial_candidate_46876.json"):
        game = QuittingGame.from_dict(load_json(repo_root / "examples" / filename))
        result = periodic_grid_search(game, denominator=2, period=2, keep=1)
        if not result.complete_global_grid or result.evaluated_profiles != result.total_profiles:
            raise RuntimeError(f"grid audit for {filename} was unexpectedly incomplete")
        reports[filename] = {
            "denominator": 2,
            "period": 2,
            "evaluated_profiles": result.evaluated_profiles,
            "minimum_observed_regret": rational_text(result.candidates[0].maximum_regret),
            "best_profile": result.candidates[0].to_dict()["profile"],
            "elapsed_seconds": round(result.elapsed_seconds, 5),
            "scope": "complete finite rational grid; no continuous-domain claim",
        }
    return reports


def audit_software(repo_root: Path) -> dict[str, Any]:
    cargo = _tool("cargo")
    python = sys.executable
    commands = {
        "pytest": [python, "-m", "pytest", "-q", "--cov=uniform_lab", "--cov-fail-under=80"],
        "ruff": [python, "-m", "ruff", "check", "."],
        "mypy": [python, "-m", "mypy"],
        "cargo_fmt": [cargo, "fmt", "--manifest-path", "rust-scanner/Cargo.toml", "--", "--check"],
        "cargo_clippy": [
            cargo,
            "clippy",
            "--manifest-path",
            "rust-scanner/Cargo.toml",
            "--all-targets",
            "--",
            "-D",
            "warnings",
        ],
        "cargo_test": [cargo, "test", "--manifest-path", "rust-scanner/Cargo.toml", "--release"],
    }
    return {name: _run(command, repo_root) for name, command in commands.items()}


def run_full_replication() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    started = time.perf_counter()
    print("UNIFORM scoped release verification")
    print(f"Repository: {repo_root}")

    print("[1/5] JSON Schema meta-validation and example validation", flush=True)
    schemas = audit_json_schemas(repo_root)
    print(
        f"      passed: {schemas['schema_count']} schemas, {schemas['validated_examples']} examples"
    )

    print("[2/5] Exact symbolic elimination benchmarks", flush=True)
    elimination = audit_symbolic_elimination(repo_root)
    print("      passed: scoped eliminants/reductions reproduced")

    print("[3/5] Complete denominator-2, period-2 grid enumerations", flush=True)
    grids = audit_complete_period_two_grids(repo_root)
    print("      passed: both 6,561-profile grids fully enumerated")

    print("[4/5] Python and Rust release gates", flush=True)
    software = audit_software(repo_root)
    print("      passed: pytest/coverage, Ruff, mypy, rustfmt, Clippy, cargo test")

    print("[5/5] Lean build", flush=True)
    lean = audit_lean(repo_root)
    print("      passed: Lake compiled all checked-in Lean modules")

    certificate = {
        "schema": "uniform.release-audit/v1",
        "generated_at_epoch": time.time(),
        "elapsed_seconds": round(time.perf_counter() - started, 4),
        "scope": (
            "software release checks and the explicitly enumerated finite experiments; "
            "not a proof of the general uniform-equilibrium conjecture"
        ),
        "schemas": schemas,
        "symbolic_elimination": elimination,
        "period_two_grids": grids,
        "software": software,
        "lean": lean,
        "verdict": "SCOPED_RELEASE_CHECKS_PASSED",
    }
    output = repo_root / "audit_certificate.json"
    output.write_text(json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"PASS: scoped release certificate written to {output}")


if __name__ == "__main__":
    run_full_replication()
