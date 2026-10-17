# Artifact evaluation guide

This guide is for reviewers evaluating the UNIFORM software artifact and its explicitly scoped finite experiments. It does not ask reviewers to accept a general uniform-equilibrium theorem.

## One-command evaluation

```bash
uv sync --frozen --extra dev --extra solvers
uv run python scripts/reproduce_all.py
```

Success produces `audit_certificate.json` with verdict `SCOPED_RELEASE_CHECKS_PASSED`. Inspect the `scope` field before interpreting any result.

## Claim-to-artifact matrix

| Check | Artifact | Independent command | Meaning |
|---|---|---|---|
| Complete quitting tensor | `examples/*.json` + schema | `uniform validate-game FILE` | Input is structurally valid |
| No pure instant equilibrium for Candidate 46876 | `lean/Uniform/AdversarialCandidate46876.lean` | `cd lean && lake build` | The concrete 16-profile Boolean theorem compiles |
| Period-2 denominator-2 minima | `grid.py` + examples | `scripts/reproduce_all.py` | Exact minimum over 6,561 enumerated profiles only |
| Three-player eliminant roots | `elimination.py` | `uniform eliminate examples/three_player_mesh.json` | Necessary interior candidate coordinates; back-substitution still required |
| Four-player reduction | `elimination.py` | `uniform eliminate examples/adversarial_candidate_46876.json` | Bivariate necessary conditions; existence is undetermined |
| 2D Bivariate interval root exclusion | `bivariate.py` + certificate | `uniform bivariate-prune examples/adversarial_candidate_46876.json` | Exact rational box branch-and-prune interval certificate |
| High-period screening ($P=3, 4$) | `rust-scanner` + output | `uniform-scan --audit-game ... --period 3/4` | Minimum regret $\ge 1.0000$ across $5.3 \times 10^5$ and $4.3 \times 10^7$ profiles |
| Machine-checked Indifference Principle | `lean/Uniform/Indifference.lean` | `cd lean && lake build` | Payoff Affine Decomposition and Indifference proved without sorry |
| Solver SAT witness | stamped artifact + model checker | `uniform solve-campaign ...` | Rational assignment passed exact re-evaluation |
| Solver UNSAT | stamped artifact | same | Solver result for the exact bounded query; native proof not semantically checked here |
| Farkas contradiction | `proofs.py` | `uniform proof-check FILE --type farkas` | Exact independent linear infeasibility check |
| Lean generator | `lean_exporter.py` | generate file, then compile with Lake | Concrete regret arithmetic and bound, not full game semantics |
| Package | wheel/sdist | `uv build && uvx twine check dist/*` | Metadata and archives are well formed |

## Reviewer cautions

- Do not replace a complete finite-grid statement with a continuous-domain statement.
- Do not treat timeout as UNSAT.
- Do not treat the SMT structural trace audit as semantic proof validation.
- Do not infer “zero axioms” from absence of `sorry`; use the actual Lean declarations and imports.
- Do not infer equilibrium existence from an eliminant root until all original equations and inequalities are back-substituted.
- Browser plots use JavaScript numbers for visualization; backend certificates serialize exact rational strings.

## Expected environment variation

Hashes and exact rational outputs are stable for identical inputs. Timings, solver versions, paths, and build-job counts may differ and are recorded only as environment metadata.
