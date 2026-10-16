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

end Uniform
