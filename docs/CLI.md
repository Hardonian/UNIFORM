# CLI reference

Run `uniform --help` or `uniform COMMAND --help` for authoritative options. Expected input and filesystem errors are printed concisely and return exit code 2.

## Validation and exact evaluation

- `validate-game GAME` — parse and validate a complete quitting-game tensor.
- `periodic GAME PROFILE [--output FILE]` — exact rational bounded-period regret.
- `algebraic-periodic GAME PROFILE [--output FILE]` — one-generator real-algebraic certificate.
- `horizon GAME PROFILE HORIZON [--start-phase N]` — finite-horizon backward induction.
- `grid GAME --denominator D --period P [...]` — deterministic rational-grid enumeration with optional sharding/cap.
- `path-check GAME PATH [--epsilon Q]` — structural and sequential finite absorption-path checks.
- `aps-polytopes GAME SETS [--steps N]` — exact rational-polytope essential APS iterations.
- `stochastic GAME PROFILE [--beta Q] [--horizon N]` — exact discounted and finite-horizon stochastic evaluation.
- `eliminate GAME [--output FILE]` — exact interior-candidate elimination. Inspect `interior_candidate_status`; three-player eliminant roots and four-player bivariate reductions are not confirmed solutions.

## SMT workflows

- `smt GAME --period P --epsilon Q --output QUERY.smt2`
- `solve QUERY.smt2 --solver {z3,cvc5} [...]`
- `solve-campaign GAME --period P --epsilon Q --output-dir DIR [...]`
- `check-model GAME MODEL --period P --epsilon Q`
- `stochastic-smt GAME --beta Q --epsilon Q --output QUERY.smt2`
- `stochastic-solve-campaign GAME --beta Q --epsilon Q --output-dir DIR [...]`
- `stochastic-check-model GAME MODEL --beta Q --epsilon Q`

SAT rational assignments are re-evaluated exactly. An UNSAT status is a bounded solver result. `--proof` retains backend-native proof text when available; the package does not semantically validate arbitrary Alethe/native SMT derivations.

## Proof and Lean utilities

- `proof-check FILE --type farkas` — independently verify an exact rational Farkas certificate.
- `proof-check FILE --type smt` — structurally audit parsed trace IDs, premise ordering, and the final contradiction marker. The JSON result always reports `semantically_verified: false`.
- `export-lean GAME PROFILE [--output FILE]` — emit a Lean file that recomputes reported rational regret identities and bounds. It does not derive phase values from the game semantics.

## Workbench and diagnostics

- `serve [--host HOST] [--port PORT] [--open]` — local unauthenticated HTTP workbench. Keep the default loopback host unless protected by an external security layer.
- `doctor` — report core and optional tool availability.
- `environment` — emit runtime/solver discovery metadata.
- `--version` — print the installed package version.

## Exit codes

- `0`: requested check or operation succeeded.
- `2`: invalid input, unavailable required backend, failed certificate/model check, or expected operational error.
- `3`: decisive solvers in a campaign disagreed.

Every certificate’s JSON `scope` and schema identifier are part of its public contract.
