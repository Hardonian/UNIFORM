module

import Mathlib.Data.Rat.Defs
import Mathlib.Tactic
import Uniform.Certificate

/-!
# Formal Machine-Checked Verification of Adversarial Candidate 46876

Candidate 46876 is a 4-player quitting game retained by a finite mixed-grid screen.
This module formally proves in Lean 4:
1. Every pure action profile (Fin 16) is unstable (violates Nash equilibrium).
2. For every pure profile, at least one player has a strictly profitable unilateral deviation.

The final declarations merely record and compare grid minima computed outside Lean. They
do not connect those constants to an enumeration theorem or to the continuous simplex.
-/

namespace Uniform.Candidate46876

open Uniform

def numPlayers : Nat := 4

def continuationPayoff : List ℚ := [0, 0, 0, 0]

-- Payoffs for absorbing masks 1..15, indexed as (mask : Fin 16) and (player : Fin 4)
def payoff : Fin 16 → Fin 4 → ℤ
  | ⟨0, _⟩, _ => 0
  | ⟨1, _⟩, ⟨0, _⟩ => 0  | ⟨1, _⟩, ⟨1, _⟩ => 4  | ⟨1, _⟩, ⟨2, _⟩ => -4 | ⟨1, _⟩, ⟨3, _⟩ => -4
  | ⟨2, _⟩, ⟨0, _⟩ => 3  | ⟨2, _⟩, ⟨1, _⟩ => 3  | ⟨2, _⟩, ⟨2, _⟩ => 2  | ⟨2, _⟩, ⟨3, _⟩ => -4
  | ⟨3, _⟩, ⟨0, _⟩ => 0  | ⟨3, _⟩, ⟨1, _⟩ => -1 | ⟨3, _⟩, ⟨2, _⟩ => 2  | ⟨3, _⟩, ⟨3, _⟩ => 4
  | ⟨4, _⟩, ⟨0, _⟩ => 1  | ⟨4, _⟩, ⟨1, _⟩ => 4  | ⟨4, _⟩, ⟨2, _⟩ => -3 | ⟨4, _⟩, ⟨3, _⟩ => 2
  | ⟨5, _⟩, ⟨0, _⟩ => -2 | ⟨5, _⟩, ⟨1, _⟩ => -3 | ⟨5, _⟩, ⟨2, _⟩ => -3 | ⟨5, _⟩, ⟨3, _⟩ => 0
  | ⟨6, _⟩, ⟨0, _⟩ => 4  | ⟨6, _⟩, ⟨1, _⟩ => -1 | ⟨6, _⟩, ⟨2, _⟩ => -4 | ⟨6, _⟩, ⟨3, _⟩ => 4
  | ⟨7, _⟩, ⟨0, _⟩ => 4  | ⟨7, _⟩, ⟨1, _⟩ => -2 | ⟨7, _⟩, ⟨2, _⟩ => 1  | ⟨7, _⟩, ⟨3, _⟩ => -3
  | ⟨8, _⟩, ⟨0, _⟩ => 3  | ⟨8, _⟩, ⟨1, _⟩ => 3  | ⟨8, _⟩, ⟨2, _⟩ => -3 | ⟨8, _⟩, ⟨3, _⟩ => -3
  | ⟨9, _⟩, ⟨0, _⟩ => -3 | ⟨9, _⟩, ⟨1, _⟩ => -3 | ⟨9, _⟩, ⟨2, _⟩ => -2 | ⟨9, _⟩, ⟨3, _⟩ => 4
  | ⟨10, _⟩, ⟨0, _⟩ => 0 | ⟨10, _⟩, ⟨1, _⟩ => -1| ⟨10, _⟩, ⟨2, _⟩ => 4 | ⟨10, _⟩, ⟨3, _⟩ => 3
  | ⟨11, _⟩, ⟨0, _⟩ => -2| ⟨11, _⟩, ⟨1, _⟩ => 2 | ⟨11, _⟩, ⟨2, _⟩ => 4 | ⟨11, _⟩, ⟨3, _⟩ => 4
  | ⟨12, _⟩, ⟨0, _⟩ => 0 | ⟨12, _⟩, ⟨1, _⟩ => -2| ⟨12, _⟩, ⟨2, _⟩ => -3| ⟨12, _⟩, ⟨3, _⟩ => -2
  | ⟨13, _⟩, ⟨0, _⟩ => -2| ⟨13, _⟩, ⟨1, _⟩ => 2 | ⟨13, _⟩, ⟨2, _⟩ => -1| ⟨13, _⟩, ⟨3, _⟩ => 0
  | ⟨14, _⟩, ⟨0, _⟩ => 1 | ⟨14, _⟩, ⟨1, _⟩ => -4| ⟨14, _⟩, ⟨2, _⟩ => -1| ⟨14, _⟩, ⟨3, _⟩ => 1
  | ⟨15, _⟩, ⟨0, _⟩ => 3 | ⟨15, _⟩, ⟨1, _⟩ => -1| ⟨15, _⟩, ⟨2, _⟩ => -3| ⟨15, _⟩, ⟨3, _⟩ => 1
  | _, _ => 0

def flipBit (mask : Fin 16) (player : Fin 4) : Fin 16 :=
  ⟨(mask.val ^^^ (1 <<< player.val)) % 16, by omega⟩

def isPureNash (mask : Fin 16) : Bool :=
  (payoff (flipBit mask ⟨0, by omega⟩) ⟨0, by omega⟩ ≤ payoff mask ⟨0, by omega⟩) &&
  (payoff (flipBit mask ⟨1, by omega⟩) ⟨1, by omega⟩ ≤ payoff mask ⟨1, by omega⟩) &&
  (payoff (flipBit mask ⟨2, by omega⟩) ⟨2, by omega⟩ ≤ payoff mask ⟨2, by omega⟩) &&
  (payoff (flipBit mask ⟨3, by omega⟩) ⟨3, by omega⟩ ≤ payoff mask ⟨3, by omega⟩)

theorem candidate_46876_no_pure_equilibrium :
    ∀ mask : Fin 16, isPureNash mask = false := by
  decide

def reportedStationaryGridMinimum : ℚ := 3 / 4

theorem reported_stationary_grid_minimum_positive :
    0 < reportedStationaryGridMinimum := by
  unfold reportedStationaryGridMinimum
  norm_num

def reportedCyclicGridMinimum : ℚ := 1

theorem reported_cyclic_grid_minimum_positive :
    0 < reportedCyclicGridMinimum := by
  unfold reportedCyclicGridMinimum
  norm_num

def reportedSolanVieilleCyclicGridMinimum : ℚ := 4 / 21

theorem reported_candidate_grid_minimum_exceeds_reported_solan_vieille_minimum :
    reportedSolanVieilleCyclicGridMinimum < reportedCyclicGridMinimum := by
  unfold reportedSolanVieilleCyclicGridMinimum reportedCyclicGridMinimum
  norm_num

end Uniform.Candidate46876
