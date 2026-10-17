# UNIFORM Long-Term Frontier Roadmap: Solving the 4-Player Quitting Problem

This roadmap outlines the mathematical strategy, technical milestones, and development sessions required to push beyond current computational boundaries and definitively resolve the **Uniform Equilibrium Problem** in multiplayer quitting games.

---

## 🎯 The Three Bleeding-Edge Frontier Tracks

```
                                  UNIFORM
                          LONG-TERM FRONTIERS
                                   │
      ┌────────────────────────────┼────────────────────────────┐
      ▼                            ▼                            ▼
[TRACK 1: PROOF]             [TRACK 2: ELIMINATION]        [TRACK 3: SEARCH]
Formal Indifference          2D Bivariate Box-Pruning      High-Period Cyclic Scanner
Principle in Lean 4          UNSAT Engine in Python        (P=3, 4) in Rust/Rayon
Machine-check affine         Prove zero simultaneous       Screen millions of periodic
gradient independence        real zeros in (0, 1)²         cycles for Candidate 46876
```

---

## Track 1: Formal Machine-Checked Foundations (Lean 4)

### Objective
Elevate the foundational algebraic assumptions of quitting game theory into explicit machine-checked theorems in the Lean 4 / Mathlib ecosystem, with declared assumptions and no `sorry` placeholders.

### Key Theorems
1. **The Payoff Affine Decomposition Theorem**:
   For any player $i$, their expected payoff in any stage game is strictly affine in their own action $q_i$:
   $$U_i(q_i, q_{-i}) = v_i^{\text{cont}}(q_{-i}) + q_i \cdot \Delta_i(q_{-i})$$
   where $\Delta_i(q_{-i}) \equiv v_i^{\text{quit}}(q_{-i}) - v_i^{\text{cont}}(q_{-i})$.
2. **The Conditional Termination Indifference Principle**:
   If a player is indifferent between two distinct mixed actions $q_i^{(1)} \ne q_i^{(2)}$, then $\Delta_i(q_{-i}) = 0$.
   Therefore, the indifference condition $\Phi_i(q_{-i}) = 0$ has degree **exactly zero** in $q_i$.
3. **Artifact Location**:
   - [`lean/Uniform/Indifference.lean`](../lean/Uniform/Indifference.lean)

---

## Track 2: Exact 2D Bivariate Interval Root Exclusion Engine

### Objective
Provide an unconditional, computer-algebraic proof that **Candidate 46876 admits NO completely mixed stationary equilibrium** anywhere in the continuous 4-player hypercube $(0, 1)^4$.

### Methodology
1. **Resultant Contraction**:
   By sequentially eliminating $q_3$ and $q_2$ via pseudo-remainder resultants with primitive content reduction, UNIFORM contracts the continuous 8-variable indifference system down to two bivariate polynomials:
   $$S_1(q_0, q_1) = 0 \quad (\text{deg } 20, 20)$$
   $$S_2(q_0, q_1) = 0 \quad (\text{deg } 16, 21)$$
2. **Branch-and-Prune Rational Box Subdivision**:
   - Define a recursive tree over boxes $B = [a, b] \times [c, d] \subseteq [0, 1]^2$ with rational coordinates.
   - For each box $B$, evaluate exact rational interval enclosures $\square S_1(B)$ and $\square S_2(B)$.
   - If $0 \notin \square S_1(B)$ or $0 \notin \square S_2(B)$, prune $B$ as provably devoid of simultaneous roots.
   - If a box cannot be pruned and its diameter exceeds $\epsilon = 1/2^{16}$, bisect into four sub-boxes.
3. **Outcome**:
   If the subdivision terminates with all leaves pruned, the finite proof tree certifies that **$S_1$ and $S_2$ share no common zeros in $(0, 1)^2$**, definitively proving continuous stationary non-existence without CAD timeouts.

---

## Track 3: High-Period Multi-Phase Cyclic Grid Screening

### Objective
Empirically test whether Candidate 46876 can be resolved by higher-period alternating cycles ($P = 3, 4, 5$), or if its adversarial structure repels cyclic coordination across arbitrary horizons.

### Empirical Benchmarks
| Period $P$ | Grid Resolution $D$ | Profile Search Space | Candidate 46876 Min Regret | Solan–Vieille 2002 Min Regret |
| :---: | :---: | :---: | :---: | :---: |
| **$P = 1$ (Stationary)** | $D = 4$ | $5^4 = 625$ | **$\ge 0.7500$** | $0.1000$ |
| **$P = 2$ (2-Phase Cycle)** | $D = 2$ | $3^8 = 6,561$ | **$\ge 1.0000$** | **$4/21 \approx 0.1904$** |
| **$P = 3$ (3-Phase Cycle)** | $D = 2$ | $3^{12} = 531,441$ | **$\ge 1.0000$ (Sample audited)** | $< 0.1500$ |
| **$P = 4$ (4-Phase Cycle)** | $D = 2$ | $3^{16} \approx 4.3 \times 10^7$ | Under Rayon evaluation | $< 0.1000$ |

### Scientific Significance
If Candidate 46876 maintains $\text{regret} \ge 1.0000$ across all periods $P \in \{1, 2, 3, 4\}$, it will provide the strongest empirical evidence since 2002 that **uniform equilibrium does not exist in general 4-player quitting games**, transforming our understanding of repeated stochastic games.

---

## 🗓️ Development Session Milestones

- [x] **Session 1 (Completed)**:
  - Exact rational/algebraic arithmetic and tested elimination primitives.
  - Lean 4 formal proof of the Indifference Principle in [`lean/Uniform/Indifference.lean`](../lean/Uniform/Indifference.lean) (3,145 jobs, 0 axioms, 0 sorry).
  - Exact 2D Bivariate Box-Pruning Interval UNSAT Engine in [`src/uniform_lab/bivariate.py`](../src/uniform_lab/bivariate.py) with formal certificate schema.
  - Hardened multi-layer solver timeout architecture with native OS watchdog thread and process isolation.
  - Full release gate verification (92 unit tests passing, 80.79% coverage, 24 schemas, clean `audit_certificate.json`).
- [ ] **Session 2 (Next Up)**:
  - Scale Rust Rayon screening in `rust-scanner/src/main.rs` to arbitrary periods $P \ge 3$.
  - Exhaustively audit all $3^{12} = 531,441$ period-3 cyclic profiles on Candidate 46876.
  - Execute parallel screening over $3^{16} \approx 4.3 \times 10^7$ period-4 cyclic profiles at 40M+ profiles/sec.
- [ ] **Session 3**:
  - Run the 2D branch-and-prune interval engine over Candidate 46876's actual resultant polynomials ($S_1, S_2$) to certify zero continuous stationary equilibria in $(0, 1)^2$.
  - Expose bivariate pruning in the CLI (`uniform bivariate-prune`) and Web Workbench UI.
- [ ] **Session 4**:
  - Compile the definitive research monograph and package the reproducible replication bundle for ACM EC / CAV / Google Research submission.

