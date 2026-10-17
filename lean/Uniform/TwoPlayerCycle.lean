module

import Mathlib.Data.Rat.Defs
import Mathlib.Tactic
import Uniform.Certificate

/-!
Formal certificate for QuittingInstance
Players: 2
Maximum regret: 0
-/

namespace GeneratedInstance

open Uniform

def numPlayers : Nat := 2
def continuationPayoff : List ℚ := [0, 0]
def maximumRegret : ℚ := 0

def phase0Values : List ℚ := [-1, -1]
def phase0BestDeviations : List ℚ := [-1, -1]
def phase0Regrets : List ℚ := [0, 0]

theorem certificate_regret_bound :
    maximumRegret ≤ (0 : ℚ) := by
  unfold maximumRegret
  decide

end GeneratedInstance
