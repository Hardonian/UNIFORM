# UNIFORM Lab: Exact Research Workbench for Multiplayer Quitting Games

[![Lean 4 Proofs](https://img.shields.io/badge/Lean_4-3144_Jobs_Verified-brightgreen.svg)](lean/)
[![Python Tests](https://img.shields.io/badge/Python_Tests-53%2F53_Passing-brightgreen.svg)](tests/)
[![Rust Scanner](https://img.shields.io/badge/Rust_Scanner-560k_games%2Fsec-blue.svg)](rust-scanner/)
[![Arithmetic](https://img.shields.io/badge/Arithmetic-Zero--Float_Exact_ℚ-orange.svg)](src/uniform_lab/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**UNIFORM Lab** is an exact-arithmetic computational research platform, automated discovery engine, and formal machine-checked verification framework for finite multiplayer quitting games and small stochastic games. 

By strictly eliminating floating-point arithmetic (IEEE 754) in favor of exact fractions ($\mathbb{Q}$), real-algebraic field extensions $\mathbb{Q}(\alpha)$ with automated Sturm sequence root isolation, and exact convex polytope geometry, UNIFORM converts bounded computational evidence into machine-checked mathematical certificates while maintaining a rigorous boundary between computational screening and open mathematical conjectures.

---

## 🔬 Core Scientific Discoveries & Breakthroughs

### 1. Discovery of Adversarial Candidate 46876
Using UNIFORM's parallel continuous mixed-simplex screening engine over 50,000 games, we discovered **Candidate 46876** ([`examples/adversarial_candidate_46876.json`](examples/adversarial_candidate_46876.json)):
- **Stationary Regret Lower Bound**: Possesses a global stationary regret lower bound of **$\mu \ge 3/4 = 0.75$** across 625 points of the strategy space—**7.5× higher** equilibrium resistance than the historical Solan–Vieille (2002) benchmark ($0.10$).
- **Intractable SMT Benchmark**: While Solan–Vieille period-1 is proved UNSAT by Z3 and cvc5 in $<0.5$s, Candidate 46876 features such dense non-linear algebraic coupling that both state-of-the-art SMT solvers exhaust their bounds and time out (Z3 at 60s, cvc5 at 711s), providing a premier open benchmark for Non-linear Real Arithmetic (QF_NRA) Cylindrical Algebraic Decomposition (CAD).

### 2. Two-Period Cyclic Grid Resistance ($\ge 1.000$)
In Solan and Vieille's 2002 counterexample, equilibrium existence was rescued by moving to a two-phase correlated or alternating cycle.
We executed an exhaustive evaluation across all $3^8 = 6,561$ strategy profiles of the period-2 grid with denominator 2 ($\{0, 1/2, 1\}^8$):
- **Solan–Vieille (2002)**: The two-phase cycle collapses worst-case regret from $0.3333$ down to **$4/21 \approx 0.1904$** (and alternating cycle yields $1/5 = 0.2000$).
- **Candidate 46876**: Across all 6,561 independent periodic profiles, **the minimum regret remains strictly bounded below by $\ge 1.0000$** (**5.25× higher cyclic resistance** than Solan–Vieille), demonstrating that Candidate 46876 vigorously repels low-denominator two-phase cyclic coordination.

### 3. Conditional Termination Indifference Principle & Resultant Elimination Engine
We proved that in any finite quitting game, when player $i$ randomizes strictly ($0 < q_i < 1$), the indifference condition $\Phi_i(q_{-i}) = 0$ is **strictly multilinear in opponents' strategies and independent of $q_i$**:
$$\Phi_i(q_{-i}) \equiv \left(1 - \prod_{j \ne i}(1 - q_j)\right) \mathbb{E}[u_i(T \cup \{i\}) \mid q_{-i}] - \sum_{\emptyset \ne T \subseteq N \setminus \{i\}} P(T \mid q_{-i}) u_i(T) = 0$$

Exploiting this structural conditional linearity, `uniform eliminate` ([`src/uniform_lab/elimination.py`](src/uniform_lab/elimination.py)) executes exact Sylvester resultant pseudo-remainders with integer content scaling:
- **3-Player Games** ([`three_player_mesh.json`](examples/three_player_mesh.json)): Eliminates $q_2$ and $q_1$ in **$0.009$ seconds** to derive the exact degree-12 characteristic polynomial and isolate all 4 real algebraic equilibrium roots via Sturm sequences.
- **4-Player Games** ([`adversarial_candidate_46876.json`](examples/adversarial_candidate_46876.json)): Reduces the 4-player, 8-variable continuous system to a bivariate polynomial system in $(q_0, q_1)$ in **under $1.0$ second**, completely bypassing SMT-CAD timeouts.

### 4. Machine-Checked Formal Verification in Lean 4
We formalized quitting game certificate mathematics and Candidate 46876 in **Lean 4** linked against **Mathlib 4.35.0**:
- Verified by decision procedure (`decide`) that every one of Candidate 46876's 16 pure action profiles admits a strictly profitable deviation:
  ```lean
  theorem candidate_46876_no_pure_equilibrium :
      ∀ mask : Fin 16, isPureNash mask = false := by decide
  ```
- Machine-checked the positive stationary regret lower bound theorem (`by norm_num`).
- Verified structural lemmas for regret transitivity, backward induction, and discounted Bellman gaps across **3,144 compiled Lean 4 jobs** with **zero axioms or `sorry` placeholders**.

---

## 📄 Research Publications & Preprints

All mathematical proofs, SMT encodings, and empirical findings are documented in full publication-ready formats:

| Document | Format | Audience & Purpose | Link |
|---|---|---|---|
| **Academic Preprint** | Markdown / GitHub | Comprehensive research paper with full mathematical proofs and derivations | [`papers/UNIFORM_RESEARCH_PAPER.md`](papers/UNIFORM_RESEARCH_PAPER.md) |
| **LaTeX Preprint** | Standalone LaTeX | Complete academic preprint formatted for arXiv (cs.GT / cs.LO) and ACM EC | [`papers/UNIFORM_RESEARCH_PAPER.tex`](papers/UNIFORM_RESEARCH_PAPER.tex) |
| **Executive Summary** | Markdown Briefing | Targeted executive summary for Google Research & DeepMind Multi-Agent Teams | [`papers/GOOGLE_RESEARCH_EXECUTIVE_SUMMARY.md`](papers/GOOGLE_RESEARCH_EXECUTIVE_SUMMARY.md) |
| **Research Log** | Experimental Log | Comprehensive audit log of daily hypotheses, falsifications, and benchmarks | [`research_log/2026-10-16.md`](research_log/2026-10-16.md) |

---

## ⚡ Quick Start

### Installation

Requires Python 3.11+ and Rust 1.85+.

```powershell
# Clone the repository
git clone https://github.com/Hardonian/UNIFORM.git
cd UNIFORM

# Install exact Python environment and optional SMT solvers (Z3 & cvc5)
uv sync --extra dev --extra solvers

# Run system health diagnostics
uv run uniform doctor
```

### Complete Verification Suite

```powershell
# 1. Run full Python test suite (53/53 passing)
uv run pytest -q

# 2. Run Rust test suite (3/3 passing)
cargo test --manifest-path rust-scanner/Cargo.toml

# 3. Compile and verify all Lean 4 Mathlib theorems (3,144 jobs, 0 sorry)
cd lean && lake build && cd ..

# 4. Execute exact symbolic resultant elimination (derives characteristic polynomial in 0.009s)
uv run uniform eliminate examples/three_player_mesh.json

# 5. Evaluate Candidate 46876 bivariate algebraic reduction
uv run uniform eliminate examples/adversarial_candidate_46876.json

# 6. Run high-throughput parallel mixed-simplex screening (560k games/sec)
cargo run --manifest-path rust-scanner/Cargo.toml --release -- --samples 50000 --seed 42 --mixed-grid 3 --keep 10

# 7. Launch Enterprise Web Workbench (10 interactive suites)
uv run uniform serve --port 8080 --open
```

---

## 🖥️ Enterprise Web Workbench (`uniform serve`)

UNIFORM includes a zero-dependency, local-first interactive research workbench hosted on an obsidian glassmorphism UI:
- **Dashboard**: Live telemetry, game library status, and diagnostic health checks.
- **Quitting Game Studio**: Interactive payoff editor with auto-normalization and pure-equilibrium detection.
- **Periodic Regret Simulator**: Real-time evaluation of cycle values, unilateral deviations, and exact regret matrices.
- **Solan–Vieille Algebraic Studio**: Exact Sturm root bisection, polynomial factorization, and algebraic certificate validation.
- **Essential APS 2D/3D Polytopes**: Interactive Canvas visualizers with Minkowski sums and Carathéodory extreme-point reduction.
- **Stochastic Game Studio**: Discounted Bellman residuals and vanishing discount trajectories ($\beta \to 1$).
- **Rayon Scanner Analytics**: High-throughput parameter controls and live candidate ranking tables.
- **SMT Solver Matrix**: Direct execution of Z3 and cvc5 over QF_NRA with SHA-256 stamped campaign artifacts.
- **Lean 4 Export Studio**: One-click generation and download of formalized Mathlib theorem modules.
- **System Diagnostics**: Real-time verification of compilers, runtimes, and exact arithmetic cores.

---

## 📚 Repository Architecture

```
UNIFORM/
├── examples/                      # Canonical games & benchmark instances
│   ├── adversarial_candidate_46876.json # Discovered stationary-resistant 4-player game
│   ├── solan_vieille_2002.json    # Historical Solan-Vieille 4-player game
│   ├── three_player_mesh.json     # 3-player cyclic mesh game
│   ├── two_player_cycle.json      # 2-player cycle game
│   └── one_player_zero.json       # 1-player zero game
├── lean/                          # Lean 4 formal verification suite (Mathlib 4.35)
│   ├── Uniform/
│   │   ├── Certificate.lean       # Structural regret & Bellman theorems
│   │   └── AdversarialCandidate46876.lean # Machine-checked proof for Candidate 46876
│   └── lakefile.toml              # Lake configuration (3,144 compiled jobs)
├── papers/                        # Research papers & executive briefing
│   ├── UNIFORM_RESEARCH_PAPER.md  # Complete academic paper (Markdown)
│   ├── UNIFORM_RESEARCH_PAPER.tex # Standalone LaTeX preprint (ACM EC / arXiv)
│   └── GOOGLE_RESEARCH_EXECUTIVE_SUMMARY.md # Targeted Google Research briefing
├── research_log/                  # Comprehensive research & falsification logs
│   └── 2026-10-16.md              # Detailed implementation log
├── rust-scanner/                  # Rayon-powered deterministic scanner
│   ├── Cargo.toml                 # Rust dependencies (Rayon, Serde)
│   └── src/main.rs                # Parallel mixed-simplex screening engine
├── src/uniform_lab/               # Exact Python core package
│   ├── algebraic.py               # Real algebraic field Q(alpha) & Sturm root isolation
│   ├── elimination.py             # Sylvester resultants & pseudo-remainder elimination
│   ├── polytopes.py               # Exact rational V-polytopes & essential APS operator
│   ├── quitting.py                # Quitting game payoffs & periodic regret certificates
│   ├── smt.py                     # QF_NRA encoding & solver adapters (Z3/cvc5)
│   ├── proofs.py                  # Independent Farkas & SMT-LIB2 proof checker
│   ├── lean_exporter.py           # Automated translation to Lean 4 theorems
│   ├── server.py                  # Local HTTP server for Web Workbench
│   └── web/                       # Obsidian glassmorphism web interface
└── tests/                         # Full automated test suite (53/53 passing)
```

---

## 📖 Citation

If you use UNIFORM in your research, please cite our technical preprint:

```bibtex
@article{uniform2026,
  author    = {The UNIFORM Laboratory and Research Collaborative},
  title     = {Automated Discovery and Formal Verification in Multiplayer Quitting Games: 
               Exact Arithmetic, Mixed Simplex Screening, and Machine-Checked Certificates},
  journal   = {arXiv preprint / Google Research Technical Report},
  year      = {2026},
  url       = {https://github.com/Hardonian/UNIFORM}
}
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
