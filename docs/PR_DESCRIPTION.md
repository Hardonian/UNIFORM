# PR: Harden UNIFORM 1.0.0 release candidate

## Summary

- optimize exact discounted and finite-horizon stochastic evaluation;
- publish schemas/examples as package resources and validate them with the Draft 2020-12 meta-schema;
- make algebraic elimination status reflect confirmation, candidate roots, or an unsolved reduction;
- restrict SMT trace checking to an honestly labelled structural audit while preserving exact Farkas checking;
- generate Lean arithmetic certificates that recompute regret identities and bounds and state their semantic boundary;
- harden the local HTTP workbench with request limits, same-origin operation, security headers, safe resource lookup, and bounded jobs;
- add version/error CLI ergonomics, Python-version CI, both SMT backends, isolated wheel tests, trusted release publishing, dependency updates, and governance files;
- replace hard-coded or globalized research claims with rerunnable, scoped evidence.

## Required verification

```bash
uv run python scripts/reproduce_all.py
uv build
uvx twine check dist/*
```

CI additionally installs the wheel in an empty environment and exercises Z3 and cvc5 on all supported Python versions.

## Research boundary

This release does not resolve general uniform-equilibrium existence. Finite-grid minima remain finite-grid facts; native SMT UNSAT proofs are retained but not semantically checked; three-player eliminant roots require back-substitution; four-player bivariate reductions do not decide existence; and generated Lean files check reported arithmetic rather than deriving values from a formal game model.
