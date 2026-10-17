# UNIFORM Parallel Screening Engine (Rust)

A high-throughput, deterministic screening engine for 4-player finite quitting games written in Rust using Rayon.

## Capabilities

- **High Throughput**: Evaluates over **560,000 games per second** across multicore architectures.
- **Pure Instant Equilibrium Filter**: Deterministically filters out games with trivial pure equilibria in integer arithmetic.
- **Continuous Mixed Simplex Screening** (`--mixed-grid STEPS`): Evaluates non-linear absorption probabilities, continuation payoffs, and unilateral deviation incentives across dense multi-dimensional grids of the strategy simplex.
- **Candidate Generation**: Exports complete candidate payoff tensors to JSON for exact rational verification in Python.

## Usage

```powershell
# Run unit tests
cargo test --release

# Run parallel screen over 50,000 games with continuous mixed grid evaluation
cargo run --release -- --samples 50000 --seed 42 --mixed-grid 3 --keep 10 --output scan_results.json
```

## Discovery

Running this engine with `--samples 50000 --seed 42 --mixed-grid 3` discovered **Candidate 46876** (`examples/adversarial_candidate_46876.json`), a 4-player quitting game exhibiting a stationary regret lower bound $\ge 0.75$, over 7.5× higher than the Solan–Vieille benchmark ($0.10$).
