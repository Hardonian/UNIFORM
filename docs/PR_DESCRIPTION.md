# PR: Build the exact UNIFORM research lab

## Summary

- implement exact rational quitting-game values, bounded-period deviations, and
  finite-horizon certificates;
- add fixed-period QF_NRA export, Z3/cvc5 execution and model parsing, and independent
  rational witness checks;
- add SHA-256-stamped multi-solver campaigns, normalized timeout/error states, separate
  raw outputs, and optional native proof retention;
- add exact one-generator real-algebraic arithmetic and certify the published
  Solan–Vieille period-two profile with exactly zero bounded-period regret;
- add deterministic exact grid enumeration with caps, shards, JSON, and CSV output;
- add exact small stochastic-game discounted and finite-horizon validators;
- add finite symbolic continuous/jump absorption paths and exact rational-polytope APS;
- transcribe the published Solan–Vieille four-player example with provenance;
- add deterministic Rayon screening, a checked-in million-game run, and exact Python
  handoff validation;
- add and build Lean certificate lemmas without proof placeholders;
- add schemas, CI, source notes, environment capture, and research log.

## Verification

- `uv run ruff check .`
- `uv run mypy`
- `uv run python -m pytest -q` — 31 passed
- `uv build` — wheel and sdist built
- 0.2.0 wheel inspection — all solver/algebraic/grid/polytope modules and 9 schemas
- `cargo fmt --check`, `cargo clippy -D warnings`, release tests — 2 passed
- `lake build` — 3,139 jobs completed
- Z3 5.3.1 and cvc5 1.4.2 rational SAT models independently rechecked
- one-million-game Rust output independently verified by Python

## Research boundary

This PR does not claim to solve equilibrium existence for four-player quitting games
or general multiplayer stochastic games. The imported denominator-2 CSV is marked
unlinked because its referenced full payoff fixture was not supplied. The exact
algebraic certificate is a single-game, period-two-class result. General multivariate
algebraic models, non-polyhedral APS sets, and independently checked UNSAT proofs remain
open. Solver UNKNOWN and bounded-class UNSAT are never promoted to global mathematical
conclusions.
