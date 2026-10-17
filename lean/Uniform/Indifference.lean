module

import Mathlib.Data.Rat.Defs
import Mathlib.Tactic

/-!
# The Conditional Termination Indifference Principle

This module proves generic rational identities used by UNIFORM's symbolic elimination engine:
a binary mixture is affine in its mixing probability. A future formal game model must connect
the conditional payoffs below to a finite quitting game before the identities become a theorem
about that game. Algebraically, equality at two distinct actions implies that the indifference condition
$\Delta_i(q_{-i}) \equiv v_i^{\text{quit}}(q_{-i}) - v_i^{\text{cont}}(q_{-i}) = 0$
holds, which has polynomial degree zero in $q_i$.
-/

namespace Uniform.Indifference

/-- Expected payoff of player i as a function of their quitting probability q_i,
    given conditional quitting payoff v_quit and conditional continuation payoff v_cont. -/
def expectedPayoff (q_i v_quit v_cont : ℚ) : ℚ :=
  q_i * v_quit + (1 - q_i) * v_cont

/-- The indifference margin between quitting and continuing. -/
def indifferenceDelta (v_quit v_cont : ℚ) : ℚ :=
  v_quit - v_cont

/-- The payoff decomposition theorem: expected payoff is identically affine in q_i. -/
theorem payoff_affine_in_own_action (q_i v_quit v_cont : ℚ) :
    expectedPayoff q_i v_quit v_cont = v_cont + q_i * (indifferenceDelta v_quit v_cont) := by
  unfold expectedPayoff indifferenceDelta
  ring

/-- When indifference holds (Delta = 0), expected payoff is completely independent of q_i. -/
theorem indifference_implies_payoff_constant
    (q_i₁ q_i₂ v_quit v_cont : ℚ)
    (h_indiff : indifferenceDelta v_quit v_cont = 0) :
    expectedPayoff q_i₁ v_quit v_cont = expectedPayoff q_i₂ v_quit v_cont := by
  rw [payoff_affine_in_own_action q_i₁]
  rw [payoff_affine_in_own_action q_i₂]
  rw [h_indiff]
  ring

/-- Conversely, if two distinct mixed actions yield equal expected payoffs,
    the player must be strictly indifferent (Delta = 0). -/
theorem equal_payoffs_distinct_actions_implies_indifference
    (q_i₁ q_i₂ v_quit v_cont : ℚ)
    (h_distinct : q_i₁ ≠ q_i₂)
    (h_eq : expectedPayoff q_i₁ v_quit v_cont = expectedPayoff q_i₂ v_quit v_cont) :
    indifferenceDelta v_quit v_cont = 0 := by
  have h1 : expectedPayoff q_i₁ v_quit v_cont = v_cont + q_i₁ * (indifferenceDelta v_quit v_cont) :=
    payoff_affine_in_own_action q_i₁ v_quit v_cont
  have h2 : expectedPayoff q_i₂ v_quit v_cont = v_cont + q_i₂ * (indifferenceDelta v_quit v_cont) :=
    payoff_affine_in_own_action q_i₂ v_quit v_cont
  rw [h1, h2] at h_eq
  have h_sub : (q_i₁ - q_i₂) * (indifferenceDelta v_quit v_cont) = 0 := by
    calc (q_i₁ - q_i₂) * (indifferenceDelta v_quit v_cont)
      _ = (v_cont + q_i₁ * (indifferenceDelta v_quit v_cont)) - (v_cont + q_i₂ * (indifferenceDelta v_quit v_cont)) := by ring
      _ = 0 := by linarith [h_eq]
  cases mul_eq_zero.mp h_sub with
  | inl h_diff =>
    exfalso
    apply h_distinct
    linarith
  | inr h_delta =>
    exact h_delta

/-- A player with positive delta strictly prefers quitting over continuing. -/
theorem positive_delta_strictly_prefers_quitting
    (v_quit v_cont : ℚ)
    (h_pos : 0 < indifferenceDelta v_quit v_cont) :
    expectedPayoff 0 v_quit v_cont < expectedPayoff 1 v_quit v_cont := by
  unfold expectedPayoff indifferenceDelta at *
  linarith

/-- A player with negative delta strictly prefers continuing over quitting. -/
theorem negative_delta_strictly_prefers_continuing
    (v_quit v_cont : ℚ)
    (h_neg : indifferenceDelta v_quit v_cont < 0) :
    expectedPayoff 1 v_quit v_cont < expectedPayoff 0 v_quit v_cont := by
  unfold expectedPayoff indifferenceDelta at *
  linarith

end Uniform.Indifference
