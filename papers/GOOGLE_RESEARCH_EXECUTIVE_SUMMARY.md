# Executive summary: exact computational infrastructure for multiplayer quitting games

**Project:** UNIFORM Research Workbench  
**Repository:** [Hardonian/UNIFORM](https://github.com/Hardonian/UNIFORM)  
**Status:** 1.0.0 release candidate; computational research artifact, not a resolution of the open uniform-equilibrium problem

UNIFORM is an exact-arithmetic platform for investigating finite multiplayer quitting games and small stochastic games. It addresses a practical problem in this research area: numerical searches, solver answers, algebraic reductions, and formal lemmas are often conflated even though they have different trust boundaries.

The workbench provides:

1. exact rational evaluation of periodic and finite-horizon profiles;
2. one-generator real-algebraic arithmetic with Sturm root isolation;
3. complete, shardable rational-grid enumeration with explicit completeness metadata;
4. Z3/cvc5 QF_NRA campaigns, hashed artifacts, and exact re-evaluation of rational SAT witnesses;
5. exact discounted stochastic-game evaluation and stationary-policy deviations;
6. rational V-polytope operators and finite symbolic absorption paths;
7. a deterministic Rayon scanner scaled to arbitrary periods $P \ge 1$, evaluating over $4.3 \times 10^7$ periodic profiles with recorded throughput;
8. an exact 2D bivariate interval branch-and-prune UNSAT engine (`uniform bivariate-prune`) operating over rational sub-boxes;
9. a Lean 4 library formalizing core regret bounds, the Payoff Affine Decomposition Theorem, and the Conditional Termination Indifference Principle (`lean/Uniform/Indifference.lean`);
10. a local browser workbench with interactive Sylvester resultant elimination and 2D box pruning action; and
11. a release audit that runs schema/example validation, complete finite experiments, Python/Rust quality gates, and `lake build`.

## Candidate 46876

Candidate 46876 is a useful adversarial benchmark selected by finite mixed-grid screening. The checked-in experiments establish exact minima on their stated grids:
- $P=1$ (Stationary, $D=4$, 625 profiles): Min regret $= 0.7500$ ($3/4$).
- $P=2$ (2-Phase Cycle, $D=2$, 6,561 profiles): Min regret $= 1.0000$.
- $P=3$ (3-Phase Cycle, $D=2$, 531,441 profiles): Min regret $\ge 1.0000$ (evaluated in $0.101$s at $5.28$M profiles/sec).
- $P=4$ (4-Phase Cycle, $D=2$, 43,046,721 profiles): Min regret $\ge 1.0000$ (evaluated in $15.37$s at $2.80$M profiles/sec).

Across all tested horizons $P \in \{1, 2, 3, 4\}$, Candidate 46876 maintains a strictly positive regret floor $\ge 1.0000$, exhibiting unprecedented resistance to multi-phase cyclic coordination.

The elimination engine derives necessary interior indifference conditions. For four-player instances it currently produces a bivariate reduction; it does not yet isolate all common roots or back-substitute them into the original system. Accordingly, stationary-equilibrium existence for Candidate 46876 remains undetermined by that component. Solver timeouts are reported as timeouts, never as UNSAT.

The Lean module proves the concrete absence of a pure equilibrium across the 16 pure profiles. It also records and compares externally computed grid constants, but those constant-arithmetic theorems are not enumeration proofs. The generated Lean certificate checks reported regret subtraction and bounds; a formal connection from game tensors to those computed values remains future work.

## Why the artifact is useful

The principal contribution is methodological: every output carries its strategy class and verification scope, rational witnesses are checked outside the solver, finite-grid completeness is machine-readable, and incomplete elimination is not labelled as a solution. This makes the repository suitable for developing and falsifying stronger conjectures without turning computational resistance into a theorem.

## Reproduce

```bash
uv sync --frozen --extra dev --extra solvers
uv run python scripts/reproduce_all.py
```

A successful run emits `SCOPED_RELEASE_CHECKS_PASSED`. See [the artifact guide](../docs/ARTIFACT_EVALUATION.md) for the claim-to-command matrix and [the long-term roadmap](../docs/ROADMAP_LONGTERM_FRONTIERS.md) for unresolved proof work.
