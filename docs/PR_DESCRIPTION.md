# PR: Build the exact UNIFORM research lab

## Summary

- implement exact rational quitting-game values, bounded-period deviations, and
  finite-horizon certificates;
- add fixed-period QF_NRA export, Z3/cvc5 execution and model parsing, and independent
  rational witness checks;
- add exact small stochastic-game discounted and finite-horizon validators;
- add finite symbolic continuous/jump absorption paths and finite-point essential APS;
- transcribe the published Solan–Vieille four-player example with provenance;
- add deterministic Rayon screening, a checked-in million-game run, and exact Python
  handoff validation;
- add and build Lean certificate lemmas without proof placeholders;
- add schemas, CI, source notes, environment capture, and research log.

## Verification

- `uv run ruff check .`
- `uv run mypy`
- `uv run python -m pytest -q` — 18 passed
- `uv build` — wheel and sdist built
- `cargo fmt --check`, `cargo clippy -D warnings`, release tests — 2 passed
- `lake build` — 3,139 jobs completed
- Z3 5.3.1 and cvc5 1.4.2 rational SAT models independently rechecked
- one-million-game Rust output independently verified by Python

## Research boundary

This PR does not claim to solve equilibrium existence for four-player quitting games
or general multiplayer stochastic games. The imported denominator-2 CSV is marked
unlinked because its referenced full payoff fixture was not supplied. The
Solan–Vieille algebraic profile is retained as a high-accuracy rational approximation;
the exact algebraic-number certification layer remains future work. Solver UNKNOWN and
bounded-class UNSAT are never promoted to global mathematical conclusions.
