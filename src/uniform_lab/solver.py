"""Solver adapters and reproducible bounded-query artifacts."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from .quitting import QuittingGame
from .rational import Q, rational_text
from .smt import independently_check_model, parse_solver_model
from .stochastic import StochasticGame
from .stochastic_smt import independently_check_stochastic_model

SolverStatus = Literal["sat", "unsat", "unknown", "timeout", "error", "missing"]


def _status(stdout: str, *, timed_out: bool, returncode: int) -> SolverStatus:
    if timed_out:
        return "timeout"
    match = re.search(r"(?m)^(sat|unsat|unknown)\s*$", stdout)
    if match:
        return match.group(1)  # type: ignore[return-value]
    return "error" if returncode else "missing"


@dataclass(frozen=True)
class SolverRun:
    solver: str
    executable: str
    version: str
    returncode: int
    stdout: str
    stderr: str
    elapsed_seconds: float = 0.0
    timed_out: bool = False
    backend: str = "command-line"
    proof: str | None = None

    @property
    def status(self) -> SolverStatus:
        return _status(self.stdout, timed_out=self.timed_out, returncode=self.returncode)

    def to_dict(self, *, include_raw: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "solver": self.solver,
            "backend": self.backend,
            "executable": self.executable,
            "version": self.version,
            "status": self.status,
            "returncode": self.returncode,
            "elapsed_seconds": self.elapsed_seconds,
            "timed_out": self.timed_out,
            "proof_available": self.proof is not None,
            "native_proof_sha256": (
                None
                if self.proof is None
                else hashlib.sha256(self.proof.encode("utf-8")).hexdigest()
            ),
        }
        if include_raw:
            payload.update({"stdout": self.stdout, "stderr": self.stderr, "proof": self.proof})
        return payload


def run_solver(
    path: str | Path, solver: str, *, timeout: float = 60.0, produce_proof: bool = False
) -> SolverRun:
    """Run a supported solver, falling back to its official Python binding.

    Timeouts are returned as structured results rather than raised.  A retained native
    proof is evidence from that solver, not automatically an independently checked proof.
    """

    if solver not in {"z3", "cvc5"}:
        raise ValueError("solver must be z3 or cvc5")
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    query = Path(path)
    executable = shutil.which(solver)
    if executable is None:
        return _run_python_binding(query, solver, timeout, produce_proof=produce_proof)
    try:
        version = subprocess.run(
            [executable, "--version"], check=False, capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except subprocess.TimeoutExpired:
        version = "version-query-timeout"
    command = [executable]
    if solver == "cvc5":
        command.append("--lang=smt2")
    command.append(str(query))
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command, check=False, capture_output=True, text=True, timeout=timeout
        )
        elapsed = time.monotonic() - started
        proof = None
        if produce_proof and _status(
            completed.stdout, timed_out=False, returncode=completed.returncode
        ) == "unsat":
            proof = _run_command_line_proof(executable, solver, query, timeout)
        return SolverRun(
            solver,
            executable,
            version,
            completed.returncode,
            completed.stdout,
            completed.stderr,
            elapsed,
            False,
            "command-line",
            proof,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return SolverRun(
            solver,
            executable,
            version,
            124,
            stdout,
            stderr or f"timeout after {timeout} seconds",
            time.monotonic() - started,
            True,
            "command-line",
        )


def _extract_native_proof(solver: str, stdout: str) -> str | None:
    if not re.search(r"(?m)^unsat\s*$", stdout):
        return None
    marker = re.search(r"(?m)^unsat\s*$", stdout)
    if marker is None:
        return None
    tail = stdout[marker.end() :].strip()
    if not tail or tail.startswith("(error"):
        return None
    return tail


def _run_command_line_proof(
    executable: str, solver: str, query: Path, timeout: float
) -> str | None:
    text = query.read_text(encoding="utf-8")
    if "(get-model)" in text:
        text = text.replace("(get-model)", "(get-proof)")
    else:
        text += "\n(get-proof)\n"
    command = [executable]
    if solver == "z3":
        command.extend(["proof=true", "-in"])
    else:
        command.extend(["--lang=smt2", "--produce-proofs"])
    try:
        completed = subprocess.run(
            command,
            input=text,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None
    if completed.returncode != 0:
        return None
    return _extract_native_proof(solver, completed.stdout)


def _run_python_binding(
    path: Path, solver: str, timeout: float, *, produce_proof: bool
) -> SolverRun:
    """Use optional official Python bindings when no command-line binary exists."""

    started = time.monotonic()
    try:
        if solver == "z3":
            import z3  # type: ignore[import-untyped]

            context = z3.Context(proof=produce_proof)
            engine = z3.Solver(ctx=context)
            engine.set(timeout=max(1, int(timeout * 1000)))
            engine.from_string(path.read_text(encoding="utf-8"))
            status = engine.check()
            stdout = str(status) + "\n"
            proof: str | None = None
            if status == z3.sat:
                stdout += engine.model().sexpr() + "\n"
            elif status == z3.unsat and produce_proof:
                proof = engine.proof().sexpr()
            elapsed = time.monotonic() - started
            timed_out = status == z3.unknown and "timeout" in engine.reason_unknown().lower()
            return SolverRun(
                solver,
                "python:z3",
                z3.get_version_string(),
                0,
                stdout,
                f"reason_unknown={engine.reason_unknown()}" if status == z3.unknown else "",
                elapsed,
                timed_out,
                "python-binding",
                proof,
            )
        import cvc5  # type: ignore[import-untyped]

        engine = cvc5.Solver()
        engine.setOption("tlimit-per", str(max(1, int(timeout * 1000))))
        if produce_proof:
            engine.setOption("produce-proofs", "true")
        parser = cvc5.InputParser(engine)
        parser.setFileInput(cvc5.InputLanguage.SMT_LIB_2_6, str(path))
        responses: list[str] = []
        last_status = ""
        while not parser.done():
            command = parser.nextCommand()
            if command.isNull():
                break
            name = command.getCommandName()
            if name == "get-model" and last_status != "sat":
                continue
            response = command.invoke(parser.getSolver(), parser.getSymbolManager())
            if response:
                rendered = str(response)
                responses.append(rendered)
                if name == "check-sat":
                    last_status = rendered.strip()
        stdout = "".join(responses)
        proof = None
        if produce_proof and re.search(r"(?m)^unsat\s*$", stdout):
            proof = "\n".join(str(item) for item in engine.getProof())
        elapsed = time.monotonic() - started
        timed_out = bool(re.search(r"(?m)^unknown\s*$", stdout)) and elapsed >= timeout * 0.9
        return SolverRun(
            solver,
            "python:cvc5",
            cvc5.__version__,
            0,
            stdout,
            "",
            elapsed,
            timed_out,
            "python-binding",
            proof,
        )
    except ImportError as exc:
        raise FileNotFoundError(
            f"{solver} executable and Python binding were not found; install the 'solvers' extra"
        ) from exc
    except Exception as exc:  # solver/parser failures must be returned with their stamp
        return SolverRun(
            solver,
            f"python:{solver}",
            "unknown",
            1,
            "",
            f"{type(exc).__name__}: {exc}",
            time.monotonic() - started,
            False,
            "python-binding",
        )


@dataclass(frozen=True)
class SolverArtifact:
    created_utc: str
    query_path: str
    query_sha256: str
    query_bytes: int
    game_sha256: str | None
    claim_scope: str
    period: int | None
    epsilon: Q | None
    parameters: Mapping[str, str]
    run: SolverRun
    model_rational_values: int
    model_unparsed_values: tuple[str, ...]
    independent_verification: Literal[
        "passed", "failed", "unverified-algebraic", "not-applicable"
    ]
    verification_note: str

    def to_dict(self, *, include_raw: bool = True) -> dict[str, Any]:
        return {
            "schema": "uniform.solver-artifact/v1",
            "created_utc": self.created_utc,
            "query": {
                "path": self.query_path,
                "sha256": self.query_sha256,
                "bytes": self.query_bytes,
                "game_sha256": self.game_sha256,
                "claim_scope": self.claim_scope,
                "period": self.period,
                "epsilon": None if self.epsilon is None else rational_text(self.epsilon),
                "parameters": dict(self.parameters),
            },
            "run": self.run.to_dict(include_raw=include_raw),
            "model": {
                "rational_value_count": self.model_rational_values,
                "unparsed_value_names": list(self.model_unparsed_values),
                "independent_verification": self.independent_verification,
                "verification_note": self.verification_note,
            },
            "trust_boundary": {
                "sat": "candidate until independently checked",
                "unsat": "bounded solver result; native proof is not independently checked here",
                "global_game_claim": False,
            },
        }


def build_solver_artifact(
    path: str | Path,
    solver: str,
    *,
    timeout: float = 60.0,
    produce_proof: bool = False,
    game: QuittingGame | None = None,
    period: int | None = None,
    epsilon: Q | None = None,
) -> SolverArtifact:
    checker: Callable[[str], bool] | None = None
    if game is not None and period is not None and epsilon is not None:
        def exact_checker(text: str) -> bool:
            return independently_check_model(game, period, epsilon, text)[2]

        checker = exact_checker
    return _build_solver_artifact(
        path,
        solver,
        timeout=timeout,
        produce_proof=produce_proof,
        period=period,
        epsilon=epsilon,
        parameters={
            "strategy_class": "independent-periodic",
            **({"period": str(period)} if period is not None else {}),
            **({"epsilon": rational_text(epsilon)} if epsilon is not None else {}),
        },
        game_payload=None if game is None else game.to_dict(),
        checker=checker,
        check_note="exact Fraction re-evaluation of all encoded same-period deviations",
    )


def build_stochastic_solver_artifact(
    path: str | Path,
    solver: str,
    *,
    game: StochasticGame,
    beta: Q,
    epsilon: Q,
    timeout: float = 60.0,
    produce_proof: bool = False,
) -> SolverArtifact:
    return _build_solver_artifact(
        path,
        solver,
        timeout=timeout,
        produce_proof=produce_proof,
        period=None,
        epsilon=epsilon,
        parameters={
            "strategy_class": "independent-stationary-discounted",
            "beta": rational_text(beta),
            "epsilon": rational_text(epsilon),
        },
        game_payload=game.to_dict(),
        checker=lambda text: independently_check_stochastic_model(
            game, beta, epsilon, text
        )[2],
        check_note="exact Fraction re-evaluation of all deterministic stationary deviations",
    )


def _build_solver_artifact(
    path: str | Path,
    solver: str,
    *,
    timeout: float,
    produce_proof: bool,
    period: int | None,
    epsilon: Q | None,
    parameters: Mapping[str, str],
    game_payload: Mapping[str, Any] | None,
    checker: Callable[[str], bool] | None,
    check_note: str,
) -> SolverArtifact:
    query_path = Path(path)
    query = query_path.read_bytes()
    run = run_solver(query_path, solver, timeout=timeout, produce_proof=produce_proof)
    parsed = parse_solver_model(run.stdout)
    verification: Literal["passed", "failed", "unverified-algebraic", "not-applicable"]
    note: str
    if run.status != "sat":
        verification, note = "not-applicable", f"solver status is {run.status}"
    elif checker is None:
        if parsed.algebraic_or_unknown:
            verification = "unverified-algebraic"
            note = "model contains values not parsed as independent rationals"
        else:
            verification = "not-applicable"
            note = "no independent checker was supplied"
    else:
        try:
            valid = checker(run.stdout)
            verification = "passed" if valid else "failed"
            note = check_note
        except (ArithmeticError, KeyError, TypeError, ValueError) as exc:
            if parsed.algebraic_or_unknown and "independently rational" in str(exc):
                verification = "unverified-algebraic"
            else:
                verification = "failed"
            note = f"independent checker rejected model: {type(exc).__name__}: {exc}"
    scope_match = re.search(r"(?m)^; SCOPE:\s*(.+)$", query.decode("utf-8"))
    scope = scope_match.group(1).strip() if scope_match else "unspecified bounded SMT query"
    game_hash = None
    if game_payload is not None:
        canonical_game = json.dumps(
            game_payload, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        game_hash = hashlib.sha256(canonical_game).hexdigest()
    return SolverArtifact(
        datetime.now(UTC).isoformat(),
        str(query_path.resolve()),
        hashlib.sha256(query).hexdigest(),
        len(query),
        game_hash,
        scope,
        period,
        epsilon,
        parameters,
        run,
        len(parsed.rationals),
        tuple(sorted(parsed.algebraic_or_unknown)),
        verification,
        note,
    )


def persist_solver_artifact(artifact: SolverArtifact, directory: str | Path) -> Path:
    output = Path(directory)
    output.mkdir(parents=True, exist_ok=True)
    stem = artifact.run.solver
    artifact_path = output / f"{stem}.artifact.json"
    artifact_path.write_text(
        json.dumps(artifact.to_dict(include_raw=False), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output / f"{stem}.stdout.txt").write_text(
        artifact.run.stdout, encoding="utf-8", newline="\n"
    )
    (output / f"{stem}.stderr.txt").write_text(
        artifact.run.stderr, encoding="utf-8", newline="\n"
    )
    if artifact.run.proof is not None:
        (output / f"{stem}.native-proof.txt").write_text(
            artifact.run.proof, encoding="utf-8", newline="\n"
        )
    return artifact_path


def campaign_summary(artifacts: list[SolverArtifact]) -> dict[str, Any]:
    statuses = {artifact.run.solver: artifact.run.status for artifact in artifacts}
    decisive = {value for value in statuses.values() if value in {"sat", "unsat"}}
    return {
        "schema": "uniform.solver-campaign/v1",
        "artifacts": [artifact.to_dict(include_raw=False) for artifact in artifacts],
        "statuses": statuses,
        "decisive_solvers_agree": len(decisive) <= 1,
        "independently_verified_sat": [
            artifact.run.solver
            for artifact in artifacts
            if artifact.independent_verification == "passed"
        ],
        "global_game_claim": False,
    }
