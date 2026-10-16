# Command reference

All probabilities and payoffs use integers or fraction strings. JSON decimal numbers
and decimal strings are rejected by the certificate loaders.

## Game and strategy certificates

- `uniform validate-game GAME` validates a complete quitting-game payoff table.
- `uniform periodic GAME PROFILE [--output FILE]` evaluates exact rational periodic
  regret from every start phase.
- `uniform algebraic-periodic GAME PROFILE [--output FILE]` validates one isolated
  algebraic generator and evaluates the same certificate symbolically.
- `uniform horizon GAME PROFILE HORIZON` performs exact finite-horizon backward
  induction.
- `uniform stochastic GAME PROFILE [--beta Q] [--horizon H]` evaluates exact
  discounted stationary and finite-horizon stochastic-game regret.

## Search and solvers

- `uniform grid GAME --denominator D --period P` exhausts the rational product grid.
  `--max-profiles` creates an explicitly incomplete run; `--shard-index I
  --shard-count K` partitions the deterministic enumeration; `--csv FILE` writes the
  retained candidates in tabular form.
- `uniform smt GAME --period P --epsilon Q --output QUERY` emits the bounded QF_NRA
  problem.
- `uniform solve QUERY --solver z3|cvc5` runs one backend. Supplying `--game`,
  `--period`, and `--epsilon` enables independent rational-model checking.
  `--output-dir DIR` separates metadata, stdout, stderr, and any native proof.
- `uniform solve-campaign GAME --period P --epsilon Q --output-dir DIR` generates one
  query and runs both solvers by default. Each artifact carries query and canonical-game
  SHA-256 hashes. Decisive disagreement returns exit code 3.
- `uniform check-model GAME MODEL --period P --epsilon Q` independently checks a saved
  rational SAT model.

Z3 and cvc5 are optional dependencies: `uv sync --extra solvers`. The adapters prefer
command-line executables and fall back to the official Python bindings. Statuses are
normalized to `sat`, `unsat`, `unknown`, `timeout`, `error`, or `missing`.

## Absorption paths and APS

- `uniform path-check GAME PATH [--epsilon Q]` validates the exact finite symbolic
  continuous/jump path and its sequential conditions.
- `uniform aps-polytopes GAME SETS [--steps N]` iterates the successor-restricted
  operator over finite unions of exact rational V-polytopes.

## Exit behavior and trust boundary

Certificate commands return 0 when their requested scoped check passes and 2 when a
candidate fails or execution fails. A solver `unknown` is retained as `unknown`; it is
not converted into UNSAT. Grid completeness fields, algebraic scope, and the
`global_game_claim=false` marker are part of the machine-readable outputs.
