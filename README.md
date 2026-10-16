# UNIFORM Lab

UNIFORM Lab is an exact-arithmetic research workbench for finite multiplayer quitting
games and small stochastic games. It turns bounded computational claims into
machine-readable certificates while keeping a hard line between evidence and a proof
of the open four-player problem.

The repository currently provides:

- strict rational quitting-game input with complete payoff-table validation;
- exact stationary and periodic payoffs, all same-period pure unilateral deviations,
  and exact truncated-horizon dynamic deviations;
- exact univariate real-algebraic arithmetic with Sturm root isolation and sign
  decisions, including a zero-regret certificate for the published period-two example;
- QF_NRA export, structured Z3/cvc5 runs, SHA-256-stamped campaign artifacts, optional
  native proof retention, and independent checking of rational SAT witnesses;
- deterministic exhaustive rational profile grids with exact regret, top-candidate CSV,
  visible completeness status, and disjoint shards for larger searches;
- exact discounted and finite-horizon validators for small finite stochastic games;
- finite symbolic absorption paths with continuous singleton hazards and product-form
  discrete jumps, plus AKRS sequential-perfectness checks;
- the 2026 successor graph, the original diagnostic point operator, and an exact
  finite-union-of-rational-polytopes essential APS operator that retains continua;
- a deterministic Rayon scanner that screens more than one million four-player games
  and hands complete candidates back to the exact Python verifier;
- a source-transcribed version of the Solan–Vieille four-player period-two example.

It does **not** claim a solution to arbitrary four-player quitting games or arbitrary
finite multiplayer stochastic games. Fixed-period UNSAT, a finite grid minimum, and a
failed local search remain restricted evidence.

## Quick start

Python 3.11+ and Rust 1.85+ are supported.

```powershell
uv sync --extra dev
# Add --extra solvers to enable local Z3 and cvc5 Python bindings.
uv run pytest -q
uv run uniform validate-game examples/solan_vieille_2002.json
uv run uniform periodic examples/solan_vieille_2002.json examples/profiles/solan_vieille_period2_rational_approx.json
uv run uniform algebraic-periodic examples/solan_vieille_2002.json examples/profiles/solan_vieille_period2_exact_algebraic.json
uv run uniform grid examples/one_player_zero.json --denominator 4 --period 1 --output grid.json --csv grid.csv
uv run uniform smt examples/solan_vieille_2002.json --period 2 --epsilon 1/1000 --output candidate.smt2
uv run uniform solve-campaign examples/one_player_zero.json --period 1 --epsilon 0 --output-dir solver-output/smoke
uv run uniform path-check examples/one_player_zero.json examples/paths/one_player_continuous.json
uv run uniform aps-polytopes examples/one_player_zero.json examples/aps/one_player_seed.json --steps 2
uv run uniform stochastic examples/stochastic/one_state_control.json examples/stochastic/one_state_half_profile.json
```

Build and run the deterministic parallel scan:

```powershell
cargo test --manifest-path rust-scanner/Cargo.toml --release
cargo run --manifest-path rust-scanner/Cargo.toml --release -- --samples 1000000 --seed 7 --keep 100 --output scan.json
uv run uniform verify-screen scan.json
```

The checked-in one-million-game run is
[`rust-scanner/benchmark_seed7.json`](rust-scanner/benchmark_seed7.json). Timing is a
host observation, not a portable benchmark.

## Conventions

Player indices are zero-based in code. Bit `i` in an outcome mask is set exactly when
player `i` quits. Mask zero means everyone continues and is not stored in the absorbing
payoff table. The `continuation` vector is used if play never absorbs and at the
boundary of explicitly truncated certificates. JSON floats are rejected; use integers
or strings such as `"7/12"`.

The algebraic profile format stores coefficients in ascending powers of one selected
real root. Its rational open interval must contain exactly one root of the square-free
defining polynomial. This handles the present benchmark and other one-generator
certificates; it is not a general multivariate real-algebraic decision procedure.

See [`docs/CERTIFICATE_MATHEMATICS.md`](docs/CERTIFICATE_MATHEMATICS.md) for the exact
claims made by each checker, [`docs/CLI.md`](docs/CLI.md) for all commands,
[`docs/RESEARCH_PROGRAM.md`](docs/RESEARCH_PROGRAM.md) for the roadmap, and
[`research_log/2026-10-16.md`](research_log/2026-10-16.md) for this implementation run.
