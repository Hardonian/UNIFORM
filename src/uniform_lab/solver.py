from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SolverRun:
    solver: str
    executable: str
    version: str
    returncode: int
    stdout: str
    stderr: str


def run_solver(path: str | Path, solver: str, *, timeout: float = 60.0) -> SolverRun:
    if solver not in {"z3", "cvc5"}:
        raise ValueError("solver must be z3 or cvc5")
    executable = shutil.which(solver)
    if executable is None:
        return _run_python_binding(Path(path), solver, timeout)
    version_flag = "--version"
    version = subprocess.run(
        [executable, version_flag], check=False, capture_output=True, text=True, timeout=10
    ).stdout.strip()
    command = [executable, str(path)] if solver == "z3" else [executable, "--lang=smt2", str(path)]
    completed = subprocess.run(
        command, check=False, capture_output=True, text=True, timeout=timeout
    )
    return SolverRun(
        solver, executable, version, completed.returncode, completed.stdout, completed.stderr
    )


def _run_python_binding(path: Path, solver: str, timeout: float) -> SolverRun:
    """Use optional official Python bindings when no command-line binary exists."""

    started = time.monotonic()
    try:
        if solver == "z3":
            import z3  # type: ignore[import-untyped]

            engine = z3.Solver()
            engine.set(timeout=max(1, int(timeout * 1000)))
            engine.from_string(path.read_text(encoding="utf-8"))
            status = engine.check()
            stdout = str(status) + "\n"
            if status == z3.sat:
                stdout += engine.model().sexpr() + "\n"
            return SolverRun(
                solver,
                "python:z3",
                z3.get_version_string(),
                0,
                stdout,
                f"elapsed_seconds={time.monotonic() - started:.6f}",
            )
        import cvc5  # type: ignore[import-untyped]

        engine = cvc5.Solver()
        engine.setOption("tlimit-per", str(max(1, int(timeout * 1000))))
        parser = cvc5.InputParser(engine)
        parser.setFileInput(cvc5.InputLanguage.SMT_LIB_2_6, str(path))
        responses: list[str] = []
        while not parser.done():
            command = parser.nextCommand()
            if command.isNull():
                break
            response = command.invoke(parser.getSolver(), parser.getSymbolManager())
            if response:
                responses.append(response)
        return SolverRun(
            solver,
            "python:cvc5",
            cvc5.__version__,
            0,
            "".join(responses),
            f"elapsed_seconds={time.monotonic() - started:.6f}",
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
        )
