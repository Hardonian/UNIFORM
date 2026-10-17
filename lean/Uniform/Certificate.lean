module

import Mathlib.Data.Rat.Defs
import Mathlib.Tactic

/-!
Established algebraic lemmas used by the external exact certificate checker.

This file intentionally proves only its stated finite arithmetic facts. It imports no
solver models and uses no proof placeholders or additional assumptions.
-/

namespace Uniform

def regret (payoff bestResponse : ℚ) : ℚ := bestResponse - payoff

theorem regret_nonnegative {payoff bestResponse : ℚ}
    (h : payoff ≤ bestResponse) : 0 ≤ regret payoff bestResponse := by
  unfold regret
  linarith

theorem regret_le_epsilon_iff (payoff bestResponse epsilon : ℚ) :
    regret payoff bestResponse ≤ epsilon ↔ bestResponse ≤ payoff + epsilon := by
  unfold regret
  constructor <;> intro h <;> linarith

theorem one_phase_cyclic_value
    (survival reward value : ℚ)
    (hSurvival : survival < 1)
    (hRecurrence : value = reward + survival * value) :
    value = reward / (1 - survival) := by
  have hne : 1 - survival ≠ 0 := ne_of_gt (sub_pos.mpr hSurvival)
  apply (eq_div_iff hne).2
  linarith

theorem convexCombination_le
    (x y bound lambda : ℚ)
    (hx : x ≤ bound) (hy : y ≤ bound)
    (hl0 : 0 ≤ lambda) (hl1 : lambda ≤ 1) :
    lambda * x + (1 - lambda) * y ≤ bound := by
  nlinarith

theorem weightedDeviationBound
    (continueValue quitValue mixedValue epsilon q : ℚ)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1)
    (hc : continueValue ≤ mixedValue + epsilon)
    (hq : quitValue ≤ mixedValue + epsilon) :
    (1 - q) * continueValue + q * quitValue ≤ mixedValue + epsilon := by
  nlinarith

theorem regret_transitivity_le
    (payoff candidate best : ℚ) (eps1 eps2 : ℚ)
    (h1 : regret payoff candidate ≤ eps1)
    (h2 : regret candidate best ≤ eps2) :
    regret payoff best ≤ eps1 + eps2 := by
  unfold regret at *
  linarith

theorem finite_horizon_backward_induction_step
    (vOld vNew payoff best_action bound : ℚ)
    (h_val : vOld ≤ payoff)
    (h_best : best_action ≤ vNew + bound) :
    regret payoff best_action ≤ regret vOld vNew + bound := by
  unfold regret
  linarith

theorem discounted_bellman_gap_le
    (val bestAction beta delta : ℚ)
    (_hBeta0 : 0 ≤ beta) (_hBeta1 : beta < 1)
    (hGap : bestAction - val ≤ delta) :
    regret val bestAction ≤ delta := by
  unfold regret
  linarith

end Uniform

