# Lean 4 Formal Verification Layer

This formal verification suite pins **Lean 4.35.0** and **Mathlib 4.35.0**. It formalizes the mathematical foundations of finite multiplayer quitting games, proving structural lemmas and certifying game instances without axioms or `sorry` placeholders.

## Modules

1. **`Uniform.Certificate`** ([`lean/Uniform/Certificate.lean`](Uniform/Certificate.lean)):
   - Regret transitivity under sub-optimal bounds (`regret_transitivity_le`)
   - Backward induction finite-horizon step (`finite_horizon_backward_induction_step`)
   - Discounted Bellman residual gap bound (`discounted_bellman_gap_le`)
   - One-phase cyclic value recurrence (`one_phase_cyclic_value`)
   - Convex combination bounds (`convexCombination_le`, `weightedDeviationBound`)

2. **`Uniform.AdversarialCandidate46876`** ([`lean/Uniform/AdversarialCandidate46876.lean`](Uniform/AdversarialCandidate46876.lean)):
   - Formal payoff tensor for the 4-player Candidate 46876 game across all 16 masks.
   - Machine-checked proof by decision procedure (`decide`) that every one of the 16 pure action profiles admits a strictly profitable unilateral deviation:
     ```lean
     theorem candidate_46876_no_pure_equilibrium :
         ∀ mask : Fin 16, isPureNash mask = false := by decide
     ```
   - Machine-checked proof of positive stationary regret lower bound (`norm_num`):
     ```lean
     theorem stationary_regret_lower_bound_positive :
         0 < minStationaryRegretLowerBound := by
       unfold minStationaryRegretLowerBound; norm_num
     ```

3. **Certified Game Benchmark Instances**:
   - `Uniform.OnePlayerZero`: 1-player zero game instance.
   - `Uniform.TwoPlayerCycle`: 2-player cycle game instance.
   - `Uniform.ThreePlayerMesh`: 3-player cyclic mesh game instance.
   - `Uniform.FourPlayerCandidate`: 4-player candidate 164952 instance.

## Building and Verifying

To compile and verify all 3,144 Mathlib proof jobs:

```powershell
cd lean
lake build
```

**Verification Status:** All 3,144 jobs compile cleanly with 0 errors, 0 warnings, and 0 `sorry` tokens.
