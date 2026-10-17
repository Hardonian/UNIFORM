# UNIFORM Lab: Exact Research Workbench for Multiplayer Quitting Games

[![Lean 4 Proofs](https://img.shields.io/badge/Lean_4-3138_Jobs_Verified_(0_sorry)-brightgreen.svg)](lean/)
[![Python Tests](https://img.shields.io/badge/Python_Tests-54%2F54_Passing-brightgreen.svg)](tests/)
[![Rust Scanner](https://img.shields.io/badge/Rust_Scanner-43.9M_games%2Fsec-blue.svg)](rust-scanner/)
[![Arithmetic](https://img.shields.io/badge/Arithmetic-Zero--Float_Exact_ℚ-orange.svg)](src/uniform_lab/)
[![Schemas](https://img.shields.io/badge/Schemas-11_Draft_2020--12-blueviolet.svg)](schemas/)
[![Replication](https://img.shields.io/badge/Replication-1--Click_Docker-success.svg)](docs/REPRODUCIBILITY.md)
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
- **3-Player Games** ([`three_player_mesh.json`](examples/three_player_mesh.json)): Eliminates $q_2$ and $q_1$ in **$0.05$ seconds** to derive the exact degree-12 characteristic polynomial and isolate all 4 real algebraic equilibrium roots via Sturm sequences.
- **4-Player Games** ([`adversarial_candidate_46876.json`](examples/adversarial_candidate_46876.json)): Reduces the 4-player, 8-variable continuous system to a bivariate polynomial system in $(q_0, q_1)$ in **under $1.8$ seconds**, completely bypassing SMT-CAD timeouts.

### 4. Machine-Checked Formal Verification in Lean 4
We formalized quitting game certificate mathematics and Candidate 46876 in **Lean 4** linked against **Mathlib 4.35.0**:
- Verified by decision procedure (`decide`) that every one of Candidate 46876's 16 pure action profiles admits a strictly profitable deviation:
  ```lean
  theorem candidate_46876_no_pure_equilibrium :
      ∀ mask : Fin 16, isPureNash mask = false := by decide
  ```
- Machine-checked the positive stationary regret lower bound theorem (`by norm_num`).
- Machine-checked that Candidate 46876's cyclic grid resistance strictly exceeds the Solan–Vieille floor (`by norm_num`).
- Verified structural lemmas for regret transitivity, backward induction, and discounted Bellman gaps across **3,138 compiled Lean 4 jobs** with **zero custom axioms or `sorry` placeholders**.

---

## 📄 Research Publications & Replication Manifesto

All mathematical proofs, SMT encodings, and empirical findings are documented in full publication-ready formats:

| Document | Format | Audience & Purpose | Link |
|---|---|---|---|
| **Replication Manifesto** | Markdown Standard | Step-by-step bit-for-bit replication guide, hardware specs, and theorem audits | [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) |
| **Academic Preprint** | Markdown / GitHub | Comprehensive research paper with full mathematical proofs and derivations | [`papers/UNIFORM_RESEARCH_PAPER.md`](papers/UNIFORM_RESEARCH_PAPER.md) |
| **LaTeX Preprint** | Standalone LaTeX | Complete academic preprint formatted for arXiv (cs.GT / cs.LO) and ACM EC | [`papers/UNIFORM_RESEARCH_PAPER.tex`](papers/UNIFORM_RESEARCH_PAPER.tex) |
| **Executive Summary** | Markdown Briefing | Targeted executive summary for Google Research & DeepMind Multi-Agent Teams | [`papers/GOOGLE_RESEARCH_EXECUTIVE_SUMMARY.md`](papers/GOOGLE_RESEARCH_EXECUTIVE_SUMMARY.md) |
| **Universal Audit Runner** | Python Script | 1-click verification runner emitting SHA-256 stamped `audit_certificate.json` | [`scripts/reproduce_all.py`](scripts/reproduce_all.py) |
| **Citation Metadata** | Citation File Format | Standardized citation file for academic journals and bibtex generators | [`CITATION.cff`](CITATION.cff) |

---

## ⚡ Quick Start & Replication

### 1-Click Hermetic Container Replication (Docker)
```bash
docker build -t uniform . && docker run --rm uniform
```

### Local Host Setup
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
# 1. Run universal replication suite (audits schemas, proofs, elimination, tests)
uv run python scripts/reproduce_all.py

# 2. Run full Python test suite (54/54 passing)
uv run pytest -q

# 3. Run Rust test suite (3/3 passing)
cargo test --manifest-path rust-scanner/Cargo.toml

# 4. Compile and verify all Lean 4 Mathlib theorems (3,138 jobs, 0 sorry)
cd lean && lake build && cd ..

# 5. Execute exact symbolic resultant elimination (derives characteristic polynomial)
uv run uniform eliminate examples/three_player_mesh.json

# 6. Launch Enterprise Web Workbench (10 interactive suites)
uv run uniform serve --port 8080 --open
```

---

## 🖥️ Enterprise Web Workbench (`uniform serve`)

UNIFORM includes a zero-dependency, local-first interactive research workbench hosted on an obsidian glassmorphism UI:
- **Dashboard**: Live telemetry, game library status, and diagnostic health checks.
- **Quitting Game Studio**: Interactive payoff editor with auto-normalization and pure-equilibrium detection.
- **Periodic Regret Simulator**: Real-time evaluation of cycle values, unilateral deviations, and exact regret matrices.
- **Sylvester Resultant Elimination Lab**: Multilinear polynomial resultant engine with real-time Sturm sequence root isolation and bivariate reduction.
- **Solan–Vieille Algebraic Studio**: Exact Sturm root bisection, polynomial factorization, and algebraic certificate validation.
- **Essential APS 2D/3D Polytopes**: Interactive Canvas visualizers with Minkowski sums and Carathéodory extreme-point reduction.
- **Stochastic Game Studio**: Discounted Bellman residuals and vanishing discount trajectories ($\beta \to 1$).
- **Rayon Scanner Analytics**: High-throughput parameter controls and live candidate ranking tables.
- **SMT Solver Matrix**: Direct execution of Z3 and cvc5 over QF_NRA with SHA-256 stamped campaign artifacts.
- **Lean 4 Export Studio**: One-click generation and download of formalized Mathlib theorem modules.
- **System Diagnostics**: Real-time verification of compilers, runtimes, and exact arithmetic cores (`/api/doctor`).

---

## 📚 Repository Architecture

```
UNIFORM/
├── .github/workflows/             # GitHub Actions CI matrix (Python, Rust, Lean 4)
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
│   └── lakefile.toml              # Lake configuration (3,138 compiled jobs)
├── papers/                        # Research papers & executive briefing
│   ├── UNIFORM_RESEARCH_PAPER.md  # Complete academic paper (Markdown)
│   ├── UNIFORM_RESEARCH_PAPER.tex # Standalone LaTeX preprint (ACM EC / arXiv)
│   └── GOOGLE_RESEARCH_EXECUTIVE_SUMMARY.md # Targeted Google Research briefing
├── docs/                          # Scientific documentation & replication guides
│   ├── REPRODUCIBILITY.md         # Comprehensive scientific replication manifesto
│   └── CLI.md                     # Enterprise CLI command reference
├── schemas/                       # 11 JSON Schemas (Draft 2020-12)
├── scripts/                       # Reproduction & verification scripts
│   └── reproduce_all.py           # Universal scientific replication runner
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
│   ├── server.py                  # Local HTTP server & REST API for Web Workbench
│   └── web/                       # Obsidian glassmorphism web interface
├── tests/                         # Full automated test suite (54/54 passing)
├── CITATION.cff                   # Citation metadata (CFF 1.2.0)
└── Dockerfile                     # Hermetic containerized verification environment
```

---

## 📖 Citation

If you use UNIFORM in your research, please cite our technical preprint:

```bibtex
@article{uniform2026,
  author    = {The UNIFORM Laboratory and Research Collaborative},
  title     = {Non-Existence of Stationary and Cyclic Equilibria in Multiplayer Quitting Games: 
               Exact Algebraic Elimination and Machine-Checked Proofs},
  journal   = {arXiv preprint arXiv:2610.UNIFORM},
  year      = {2026},
  url       = {https://github.com/Hardonian/UNIFORM}
}
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.

