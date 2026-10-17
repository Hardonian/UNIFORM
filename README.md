# UNIFORM Lab

[![CI](https://github.com/Hardonian/UNIFORM/actions/workflows/ci.yml/badge.svg)](https://github.com/Hardonian/UNIFORM/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)

UNIFORM Lab is an exact-arithmetic research workbench for finite multiplayer quitting games and small stochastic games. It combines rational and univariate real-algebraic arithmetic, bounded-period regret certificates, exhaustive rational grids, QF_NRA solver campaigns, exact rational polytopes, a deterministic Rust scanner, and a Lean 4 library.

The package is deliberately scoped. A finite grid minimum is evidence about that grid, an SMT result is about the emitted bounded formula, and an elimination polynomial supplies necessary interior-candidate conditions unless back-substitution is completed. None of these artifacts alone proves or disproves the general uniform-equilibrium conjecture.

## Install

Python 3.11 or newer is required.

```bash
python -m pip install uniform-lab
uniform --version
uniform doctor
```

For a source checkout with both optional SMT backends:

```bash
uv sync --frozen --extra dev --extra solvers
uv run uniform validate-game examples/one_player_zero.json
```

Rust and Lean are optional for the Python package. They are required for the complete repository release gate.

## What is independently checked?

| Component | Exact scope | Important boundary |
|---|---|---|
| Periodic certificate | Values and all deterministic unilateral policies of the stated period | Does not cover arbitrary nonperiodic strategies |
| Finite grid | Every profile on the stated rational grid when `complete_global_grid` is true | Does not establish a continuous-domain lower bound |
| SAT model check | Solver assignments re-evaluated with Python `Fraction` arithmetic | Algebraic/unparsed values are rejected |
| UNSAT result | Stamped bounded solver result; optional native proof is retained | Native SMT proof semantics are not independently checked |
| Farkas certificate | Exact `λ ≥ 0`, `λᵀA = 0`, and `λᵀb < 0` checks | Applies only to linear systems |
| SMT trace audit | Unique IDs, backward premise references, and final contradiction marker | Explicitly not a semantic Alethe proof checker |
| Lean export | Recomputes reported rational regrets and their common bound | Does not derive values from the game/profile semantics |
| Elimination | Exact resultants and isolated univariate eliminant roots | Three-/four-player outputs require back-substitution to confirm solutions |
| 2D Bivariate Engine | Exact branch-and-prune box interval UNSAT certificate | Certified absence of roots over rational sub-boxes in $(0, 1)^2$ |
| Lean library | The checked-in theorem statements compiled by Lake/Mathlib | Includes Affine Decomposition and Indifference Principle without sorry |

## Common workflows

```bash
# Exact bounded-period certificate
uniform periodic GAME.json PROFILE.json

# Complete rational-grid enumeration
uniform grid GAME.json --denominator 2 --period 2 --output grid.json

# Export, run, stamp, and cross-check Z3 and cvc5
uniform solve-campaign GAME.json --period 2 --epsilon 1/10 \
  --solvers z3 cvc5 --output-dir solver-output/run

# Discounted stationary stochastic-game campaign
uniform stochastic-solve-campaign GAME.json --beta 9/10 --epsilon 1/20 \
  --solvers z3 cvc5 --output-dir solver-output/stochastic

# Exact symbolic elimination (interior stationary candidates)
uniform eliminate GAME.json

# Exact 2D bivariate interval branch-and-prune root exclusion
uniform bivariate-prune GAME.json --max-evaluations 500

# Local browser workbench; loopback is the safe default
uniform serve --host 127.0.0.1 --port 8080 --open
```

Run `uniform --help` and see [docs/CLI.md](docs/CLI.md) for the complete command surface. JSON interfaces are versioned in [schemas](schemas); those schemas and representative examples are bundled in the wheel and available through `uniform_lab.load_schema()` and `uniform_lab.load_example()`.

## Candidate experiments

The repository includes two complete denominator-2, period-2 enumerations, each containing 6,561 independent periodic profiles:

- `examples/solan_vieille_2002.json`
- `examples/adversarial_candidate_46876.json`

The observed minima are exact for those finite grids and the stated same-period deviation class. They are not advertised as global lower bounds over the continuous strategy space. `scripts/reproduce_all.py` reruns the enumerations instead of trusting checked-in numbers.

## Repository release gate

```bash
uv sync --frozen --extra dev --extra solvers
uv run pytest -q --cov=uniform_lab --cov-fail-under=80
uv run ruff check .
uv run mypy

cargo fmt --manifest-path rust-scanner/Cargo.toml -- --check
cargo clippy --manifest-path rust-scanner/Cargo.toml --all-targets -- -D warnings
cargo test --manifest-path rust-scanner/Cargo.toml --release

cd lean && lake build && cd ..
uv run python scripts/reproduce_all.py
uv build
uvx twine check dist/*
```

The audit runner writes `audit_certificate.json` with hashes and a `SCOPED_RELEASE_CHECKS_PASSED` verdict. Timing and timestamps are informative metadata, not reproducibility claims.

The included Dockerfile provides a pinned verification environment:

```bash
docker build -t uniform-release .
docker run --rm uniform-release
```

## Development and release status

`1.0.0rc1` is the API-stabilization release candidate. See [CHANGELOG.md](CHANGELOG.md), [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md).

The project is licensed under Apache-2.0.
