# Reproducibility

UNIFORM separates deterministic mathematical outputs from environment-dependent metadata. Exact rational results and file hashes should reproduce; wall-clock timings, timestamps, executable paths, and solver versions need not.

## Pinned source environment

```bash
git clone https://github.com/Hardonian/UNIFORM.git
cd UNIFORM
uv sync --frozen --extra dev --extra solvers
```

The Python dependency graph is locked in `uv.lock`, Rust dependencies in `rust-scanner/Cargo.lock`, and Lean/Mathlib in `lean/lean-toolchain` and `lean/lake-manifest.json`.

## Complete release verification

```bash
uv run python scripts/reproduce_all.py
```

The command performs actual Draft 2020-12 meta-schema checks, validates versioned examples, reproduces scoped eliminants, enumerates both complete 6,561-profile grids, runs Python coverage/Ruff/mypy, runs Rust formatting/Clippy/tests, and invokes `lake build`. It writes `audit_certificate.json` only after every gate passes.

The certificate verdict is `SCOPED_RELEASE_CHECKS_PASSED`. Its scope explicitly excludes a proof of the general uniform-equilibrium conjecture, a continuous-domain interpretation of finite-grid minima, semantic checking of native SMT proofs, and confirmation of un-back-substituted eliminant roots.

## Individual gates

```bash
uv run pytest -q --cov=uniform_lab --cov-fail-under=80
uv run ruff check .
uv run mypy
uv run uniform solve-campaign examples/one_player_zero.json \
  --period 1 --epsilon 0 --solvers z3 cvc5 --output-dir solver-output/smoke

cargo fmt --manifest-path rust-scanner/Cargo.toml -- --check
cargo clippy --manifest-path rust-scanner/Cargo.toml --all-targets -- -D warnings
cargo test --manifest-path rust-scanner/Cargo.toml --release

cd lean && lake build && cd ..
uv build
uvx twine check dist/*
```

## Container

```bash
docker build -t uniform-release .
docker run --rm uniform-release
```

The container pins the requested Rust and uv versions and Lean pins its own toolchain. Upstream base-image and installer content should be digest-pinned by archival users who require byte-identical environments. The project does not label timing-bearing output “bit-for-bit reproducible.”

## Interpreting benchmark artifacts

Throughput depends on CPU, compiler, power state, and invocation parameters. Report the complete command, hardware, compiler version, sample count, seed, and elapsed time. A checked-in benchmark is evidence for that recorded run, not a universal performance guarantee.

Grid outputs are exhaustive only if `complete_global_grid` is true and `evaluated_profiles == total_profiles`. Solver artifacts bind results to the SHA-256 hash of the exact SMT query. Lean claims are limited to the theorem statements in the modules that Lake actually compiled.
