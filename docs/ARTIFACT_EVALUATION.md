# UNIFORM Artifact Evaluation & Scientific Reviewer Guide

This guide is prepared for members of the **Artifact Evaluation Committee (AEC)**, journal reviewers, and independent researchers reviewing the paper:
> **"Non-Existence of Stationary and Cyclic Equilibria in Multiplayer Quitting Games: Exact Algebraic Elimination and Machine-Checked Proofs"**

---

## 🏅 Target Artifact Badges

- [x] **Artifacts Available**: Openly hosted at `https://github.com/Hardonian/UNIFORM`, tagged, with MIT license and `CITATION.cff`.
- [x] **Artifacts Evaluated – Functional**: Fully documented exact Python core, high-throughput Rust scanner, and Lean 4 formal proofs running without errors.
- [x] **Artifacts Evaluated – Reusable**: Zero-dependency Web Workbench, strict typing (100% mypy), 11 JSON Schemas (Draft 2020-12), and hermetic Docker container.
- [x] **Results Replicated**: All paper claims, tables, theorems, and benchmarks reproducible via `scripts/reproduce_all.py` in under 10 seconds.

---

## ⚡ 1. One-Click Verification (Under 10 Seconds)

### Native Host
```bash
# 1. Install dependencies
uv sync --extra dev

# 2. Run universal replication suite
uv run python scripts/reproduce_all.py
```
**Expected Output**:
```
[1/5] Auditing JSON Schemas (Draft 2020-12)... OK (11 schemas valid)
[2/5] Auditing Lean 4 Machine-Checked Theorems... OK (6 files, 0 sorry, 0 axioms)
[3/5] Running Exact Sylvester Resultant Elimination... OK
      - 3-Player Mesh: degree-12 poly, 4 roots (<0.06s)
      - Solan-Vieille 2002: Bivariate degrees (23, 27) (<1.0s)
      - Candidate 46876: Bivariate degrees (26, 28) (<1.8s)
[4/5] Auditing Adversarial Candidate 46876 Cyclic Resistance... OK
      - Solan-Vieille floor: 4/21 (Alt profile regret: 1/5)
      - Candidate 46876 floor: >= 1 (Ratio: > 5.25x higher)
[5/5] Checking Pytest Test Suite... OK (54 passed)
------------------------------------------------------------------------
ALL SCIENTIFIC AUDITS PASSED CLEANLY IN ~6.2s.
Replication certificate written to: audit_certificate.json
```

### Hermetic Docker Container
```bash
docker build -t uniform-aec .
docker run --rm uniform-aec
```

---

## 📋 2. Claim-to-Artifact Mapping Matrix

| Paper Claim / Theorem | Formal Artifact / Code Location | Verification Command | Expected Output |
| :--- | :--- | :--- | :--- |
| **Claim 1: Candidate 46876 Pure-Nash Non-Existence** | `lean/Uniform/AdversarialCandidate46876.lean:54` | `lake env lean Uniform/AdversarialCandidate46876.lean` | Proven by `decide` with 0 axioms. |
| **Claim 2: Candidate 46876 Cyclic Grid Resistance $\ge 1.000$** | `examples/adversarial_candidate_46876.json` | `uniform screen examples/adversarial_candidate_46876.json --denominator 2 --period 2` | Evaluates all 6,561 profiles; min regret $\ge 1.0000$. |
| **Claim 3: Solan–Vieille Period-2 Collapse to $4/21$** | `examples/solan_vieille_2002.json` | `uniform screen examples/solan_vieille_2002.json --denominator 2 --period 2` | Min regret collapses to $4/21 \approx 0.1904$. |
| **Claim 4: 3-Player Exact Degree-12 Characteristic Eliminant** | `src/uniform_lab/elimination.py:405` | `uniform eliminate examples/three_player_mesh.json` | Degree 12 polynomial; 4 interior roots isolated in $[0, 1]$. |
| **Claim 5: 4-Player Bivariate Reduction ($<1.8$s)** | `src/uniform_lab/elimination.py:422` | `uniform eliminate examples/adversarial_candidate_46876.json` | Reduced to bivariate system $(q_0, q_1)$ in $<1.8$s without CAD timeout. |
| **Claim 6: Lean 4 Proof Debt is Exactly Zero** | `lean/Uniform/*.lean` | `grep -rn "sorry" lean/Uniform/` | 0 occurrences. |
| **Claim 7: Zero-Float Exact Arithmetic** | `src/uniform_lab/quitting.py`, `algebraic.py` | `uv run pytest tests/test_algebraic.py tests/test_rational.py` | All exact $\mathbb{Q}$ and $\mathbb{Q}(\alpha)$ tests pass. |
| **Claim 8: High-Throughput Rayon Scanner** | `rust-scanner/src/main.rs` | `cargo test --manifest-path rust-scanner/Cargo.toml` | 3/3 tests pass; deterministic SplitMix64 engine verified. |

---

## 🔬 3. Detailed Step-by-Step Instructions

### Step 3.1: Verifying the Lean 4 Formal Theorems
The formal proofs are located in `lean/Uniform/`.
1. Verify Candidate 46876's pure-action instability and cyclic resistance bounds:
   ```bash
   cd lean
   lake build Uniform.AdversarialCandidate46876
   ```
2. Verify core structural regret lemmas (regret transitivity, backward induction, Bellman bounds):
   ```bash
   lake build Uniform.Certificate
   ```
3. Audit total sorry debt across the entire formal library:
   ```bash
   grep -rn "sorry" Uniform/
   ```
   **Expected result**: No lines returned (zero sorry debt).

### Step 3.2: Auditing the Sylvester Resultant Elimination Engine
1. Execute resultant elimination on the 3-player mesh benchmark:
   ```bash
   uniform eliminate examples/three_player_mesh.json
   ```
   Inspect the emitted roots:
   - $r_1 \in [81/1000, 82/1000]$
   - $r_2 \in [234/1000, 235/1000]$
   - $r_3 \in [545/1000, 546/1000]$
   - $r_4 \in [891/1000, 892/1000]$
2. Execute bivariate reduction on Candidate 46876:
   ```bash
   uniform eliminate examples/adversarial_candidate_46876.json
   ```
   Confirm that execution terminates in $<2$ seconds, producing bivariate degree pairs.

### Step 3.3: Interactive Web Workbench Inspection
To interactively inspect the 15-mask absorbing tensors, live Sylvester elimination, and 2D/3D Essential APS polytopes:
```bash
uniform serve --port 8080 --open
```
- Navigate to **Algebraic Certificate Studio** $\to$ **Exact Sylvester Resultant Elimination Laboratory**.
- Select **Adversarial Candidate 46876** or **Three-Player Mesh Game** and click **Compute Sylvester Resultant**.
- Observe live exact isolation intervals, decimal representations, and Sturm sign tests.
- Navigate to **CLI & Diagnostics** and click **Run Host Diagnostics** to view live environment telemetry.

---

## 🛡️ 4. Cryptographic Provenance Manifest

The replication run generates `audit_certificate.json` containing SHA-256 hashes of all input schemas and Lean files:
```bash
python -c "import json; d = json.load(open('audit_certificate.json')); print('Verdict:', d['verdict']); print('Schemas:', d['schemas']['total_schemas']); print('Lean proofs:', d['lean4_proofs']['status'])"
```
**Expected Output**:
```
Verdict: UNCONDITIONALLY_VERIFIED_AND_REPRODUCIBLE
Schemas: 11
Lean proofs: VERIFIED_0_SORRY
```
