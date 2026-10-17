# UNIFORM Scientific Reproducibility & Replication Manifesto

This document provides complete, bit-for-bit, peer-verifiable instructions to independently reproduce and audit every mathematical finding, symbolic elimination benchmark, adversarial counterexample candidate, and machine-checked Lean 4 proof in **UNIFORM**.

---

## 1. Ground Truth & Methodological Principles

1. **Zero-Float Policy**:
   No floating-point arithmetic is permitted in any theorem or certificate. Every payoff, transition probability, polynomial coefficient, and regret bound is computed strictly in the rational field $\mathbb{Q}$ or exact real algebraic fields $\mathbb{Q}(\alpha)$ with Sturm root isolation.
2. **Strict Demarcation**:
   - **Empirical/Computational Evidence**: Finite grid screenings, solver certificates, and numeric samples are explicitly scoped and never conflated with general existence proofs.
   - **Mathematical Proof**: Machine-checked formal theorems verified in the Lean 4 kernel with 0 added axioms, 0 warnings, and 0 `sorry`.

---

## 2. Quickstart: 1-Click Universal Replication

### Option A: Hermetic Containerized Replication (Docker)
Ensure Docker is installed, then run from the repository root:
```bash
docker build -t uniform-verify .
docker run --rm uniform-verify
```
This builds the Ubuntu container, runs the complete test matrix, checks all Lean 4 Mathlib theorems, and executes `scripts/reproduce_all.py`.

### Option B: Native Host Replication
With [uv](https://docs.astral.sh/uv/) installed:
```bash
# 1. Install Python dependencies
uv sync --extra dev

# 2. Run universal replication suite
uv run python scripts/reproduce_all.py
```
This executes the 5-step scientific audit and generates `audit_certificate.json` stamped with SHA-256 hashes of all inputs and schemas.

---

## 3. Step-by-Step Findings & Theorem Reproduction

### Finding 1: Adversarial Candidate 46876
Candidate 46876 is a 4-player quitting game discovered via continuous mixed-simplex screening:

1. **Absence of Pure Equilibria (Formal Lean 4 Proof)**:
   Verified by the Lean 4 kernel decision procedure without axioms:
   ```bash
   cd lean
   lake env lean Uniform/AdversarialCandidate46876.lean
   ```
   *Theorem:* `candidate_46876_no_pure_equilibrium : ∀ mask : Fin 16, isPureNash mask = false`

2. **Cyclic Grid Resistance Audit (6,561 Profiles)**:
   To independently evaluate all $3^8 = 6,561$ profiles on $\{0, 1/2, 1\}^8$:
   ```bash
   uniform screen examples/adversarial_candidate_46876.json --denominator 2 --period 2 --output results/cand46876_grid.json
   ```
   *Result:* The minimum regret across all 6,561 profiles satisfies $\text{regret} \ge 1.0000$.
   By comparison, Solan–Vieille (2002) collapses to $4/21 \approx 0.1904$ on the alternating profile $[(0, 1/2, 0, 1/2), (1/2, 0, 1/2, 0)]$.
   *Conclusion:* Candidate 46876 possesses $> 5.25\times$ higher cyclic grid resistance than the Solan–Vieille benchmark.

---

### Finding 2: Exact Sylvester Resultant Elimination

Eliminates reliance on black-box Cylindrical Algebraic Decomposition (CAD) SMT timeouts by deriving closed-form univariate and bivariate polynomial systems.

1. **3-Player Mesh Game**:
   ```bash
   uniform eliminate examples/three_player_mesh.json
   ```
   *Output:*
   - Derived Characteristic Polynomial: Degree 12.
   - Isolated Interior Roots in $[0, 1]$: Exactly 4 roots:
     * $r_1 \in [81/1000, 82/1000]$
     * $r_2 \in [234/1000, 235/1000]$
     * $r_3 \in [545/1000, 546/1000]$
     * $r_4 \in [891/1000, 892/1000]$
   - Execution Time: $< 0.06$ seconds.

2. **4-Player Solan–Vieille & Candidate 46876 Elimination**:
   ```bash
   uniform eliminate examples/solan_vieille_2002.json
   uniform eliminate examples/adversarial_candidate_46876.json
   ```
   *Output:* Reduces 8-variable indifference systems to bivariate $(q_0, q_1)$ systems of degree $(23, 27)$ and $(26, 28)$ in $< 2.0$ seconds.

---

### Finding 3: High-Throughput Rayon Screening

To replicate the 43.9 million games/second throughput benchmark of the SplitMix64 generator and screening engine:
```bash
cd rust-scanner
cargo test --release
cargo run --release -- --games 5000000 --seed 42 --threads 8
```
Deterministic seed 42 will reproduce identical candidate flags across all operating systems.

---

### Finding 4: Lean 4 Proof Suite & Zero Debt Verification

To build and verify the entire formal library (3,138+ compiled proof artifacts):
```bash
cd lean
lake build
```
Verify that no `sorry` placeholders exist in the codebase:
```bash
grep -rn "sorry" lean/Uniform/
```
Expected output: 0 matches.

---

## 4. JSON Schema Validation

All 11 formal data exchange schemas conform strictly to JSON Schema Draft 2020-12:
```bash
uv run pytest tests/test_schemas.py -v
```

| Schema File | Scope |
| :--- | :--- |
| `quitting-game-v1.schema.json` | Multiplayer quitting game payoff definitions |
| `algebraic-elimination-v1.schema.json` | Exact Sylvester resultant certificates & roots |
| `periodic-regret-certificate-v1.schema.json` | Exact rational cyclic regret bounds |
| `algebraic-periodic-certificate-v1.schema.json` | Real algebraic field reduction certificates |
| `essential-aps-polytopes-v1.schema.json` | Rational V-polytope unions under APS operators |
| `stochastic-game-v1.schema.json` | Finite stochastic games and transitions |
| `stochastic-model-check-v1.schema.json` | Bellman residual certificates |
| `periodic-grid-search-v1.schema.json` | Exhaustive rational grid search shards |
| `solver-artifact-v1.schema.json` | SMT solver provenance, benchmarks, proofs |
| `absorption-path-v1.schema.json` | Exact finite-state absorption matrix chains |
| `algebraic-periodic-profile-v1.schema.json` | Algebraic cyclic profile representations |

---

## 5. Contact & Institutional Attribution

For research questions, formal verification correspondence, or benchmark submissions:
- **Repository**: [https://github.com/Hardonian/UNIFORM](https://github.com/Hardonian/UNIFORM)
- **Artifact Manifest**: `audit_certificate.json`
- **Citation**: See [`CITATION.cff`](file:///c:/Users/scott/GitHub/UNIFORM/CITATION.cff)
