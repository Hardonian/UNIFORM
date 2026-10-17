# Changelog

This project follows Semantic Versioning and keeps versioned JSON schema identifiers stable within a major schema version.

## 1.0.0rc1 — 2026-10-16

- Added exact quitting-game, algebraic, stochastic-game, rational-polytope, grid, solver-campaign, Rust scanning, Lean, and local workbench components.
- Optimized stochastic regret evaluation by reusing induced kernels and solving only the deviating player's discounted system.
- Bundled versioned schemas and top-level examples in wheels with a public resource API.
- Hardened the local HTTP service with request limits, same-origin operation, security headers, strict JSON handling, and bounded grid requests.
- Replaced the unsound SMT “proof verification” claim with an explicitly structural trace audit; retained exact independent Farkas checking.
- Strengthened generated Lean certificates to recompute regret identities and bounds while documenting that game semantics remain outside the generated theorem.
- Changed elimination output to distinguish confirmed two-player interior solutions from unconfirmed eliminant roots and unsolved bivariate reductions.
- Added multi-version CI, both optional solver backends, isolated wheel smoke tests, release automation, dependency updates, and a scoped full-stack audit runner.
- Corrected documentation that previously promoted finite-grid observations or text scans as global or machine-checked conclusions.

## 0.3.0

- Added discounted stochastic-game SMT campaigns and exact model checking.
- Added exact rational polytope canonicalization and bounded periodic-grid search.

## 0.2.0

- Added univariate algebraic arithmetic and exact periodic certificates.

## 0.1.0

- Initial exact quitting-game workbench and Rust screening engine.
