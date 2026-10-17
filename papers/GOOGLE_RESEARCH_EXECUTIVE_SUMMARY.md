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
7. a deterministic Rayon scanner whose throughput is recorded per benchmark rather than presented as a universal rate;
8. a Lean 4 library for the theorem statements actually formalized, plus generated arithmetic certificates;
9. a local browser workbench whose plots are labelled as approximate and whose backend certificates use exact rational strings; and
10. a release audit that runs schema/example validation, complete finite experiments, Python/Rust quality gates, and `lake build`.

## Candidate 46876

Candidate 46876 is a useful adversarial benchmark selected by finite mixed-grid screening. The checked-in experiments establish exact minima on their stated grids—for example, the complete denominator-2, period-2 grid has 6,561 profiles. They do not establish a lower bound on the continuous strategy cube.

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
