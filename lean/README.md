# Lean 4 layer

The library pins Lean 4 and Mathlib 4.35.0. `lake build` compiles the theorem statements checked into this directory. Build-job counts are environment-dependent and are not used as theorem counts.

## Modules

- `Uniform.Certificate` proves general rational-arithmetic identities used when reasoning about regret, convex combinations, a one-phase recurrence, and simple bounds.
- `Uniform.Indifference` proves that a binary rational mixture is affine and that equality at two distinct mixing probabilities forces a zero coefficient. It is not yet connected to a formal finite-game model.
- `Uniform.AdversarialCandidate46876` encodes a concrete payoff table and proves by decision procedure that none of its 16 pure profiles is a pure equilibrium. Its reported grid constants are data declarations; the comparison theorems do not formalize the external enumeration.
- `Uniform.OnePlayerZero`, `Uniform.TwoPlayerCycle`, `Uniform.ThreePlayerMesh`, and `Uniform.FourPlayerCandidate` contain small concrete arithmetic facts.

The Python Lean exporter produces files that recompute reported rational regrets as `bestDeviation - value` and prove that every listed regret is bounded by the reported maximum. Generated files do not derive values from a game tensor or formalize arbitrary deviations.

## Build

```bash
cd lean
lake build
```

The release audit also scans checked-in Lean sources for `sorry`, but the authoritative check is the Lake build. Absence of `sorry` does not imply absence of imported axioms or completion of the broader game-theory formalization.
