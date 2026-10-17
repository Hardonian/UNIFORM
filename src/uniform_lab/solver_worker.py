import json
import os
import sys
import threading
import time
from pathlib import Path

from .solver import _run_python_binding_direct


def _watchdog(limit_seconds: float) -> None:
    time.sleep(limit_seconds)
    os._exit(124)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 4:
        print("usage: solver_worker PATH {z3,cvc5} TIMEOUT {0,1}", file=sys.stderr)
        return 2
    path, solver, timeout_text, proof_text = args
    timeout_val = float(timeout_text)
    # Start internal watchdog thread that guarantees termination even if native library deadlocks
    watchdog = threading.Thread(target=_watchdog, args=(timeout_val + 2.0,), daemon=True)
    watchdog.start()
    try:
        run = _run_python_binding_direct(
            Path(path), solver, timeout_val, produce_proof=proof_text == "1"
        )

    except FileNotFoundError as exc:
        print(
            json.dumps(
                {
                    "solver": solver,
                    "executable": f"python:{solver}",
                    "version": "unavailable",
                    "returncode": 127,
                    "stdout": "",
                    "stderr": str(exc),
                    "elapsed_seconds": 0.0,
                    "timed_out": False,
                    "proof": None,
                }
            )
        )
        return 0
    print(
        json.dumps(
            {
                "solver": run.solver,
                "executable": run.executable,
                "version": run.version,
                "returncode": run.returncode,
                "stdout": run.stdout,
                "stderr": run.stderr,
                "elapsed_seconds": run.elapsed_seconds,
                "timed_out": run.timed_out,
                "proof": run.proof,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
