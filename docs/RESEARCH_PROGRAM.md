# Research program

The priority question is whether every finite-player quitting game, particularly with
four or more players, admits ordinary independent-strategy approximate equilibria.
The broader target is uniform equilibrium in arbitrary finite multiplayer stochastic
games. Both remain research problems; correlated and sunspot equilibria concern games
with extra randomization devices and are not substitutes.

## Track A: quitting games

1. Reproduce cited examples with their full payoff arrays and conventions.
2. Classify exact low-period candidates with QF_NRA, independently checking rational
   witnesses and treating algebraic values explicitly.
3. Keep pure, stationary mixed, periodic mixed, and arbitrary nonperiodic failures
   separate. Numerical failure is not nonexistence.
4. Work with absorption paths that retain continuous hazards and discrete jumps, then
   evaluate the essential APS operator without collapsing its set-valued geometry.
5. Search for an invariant continuation-payoff family preserved without a public
   randomization device; falsify every candidate lemma on adversarial games.
6. A positive resolution must cover every rational game and every epsilon, extend to
   real payoffs only with a justified continuity argument, and include uniform-horizon
   estimates. A negative resolution must bound deviations for every behavioral profile,
   not merely periodic ones.

## Track B: finite stochastic games

Validate discounted stationary and finite-horizon calculations; reproduce established
two-player constructions; seek statewise continuation invariants and punishments that
survive vanishing discount; prove any reduction from absorbing to multistate games
before relying on it.

## Evidence ladder

| Artifact | Status |
|---|---|
| Numerical low-regret profile | heuristic candidate |
| Exact rational certificate for one game | single-instance result |
| QF_NRA UNSAT for period `p` | exclusion of the encoded class |
| Parameterized proved family | class theorem, subject to independent review |
| Explicit game with global regret lower bound | negative resolution |
| Uniform construction for every finite game and epsilon | positive resolution |

## Engineering milestones

- M1: exact quitting engine, periodic deviations, horizons, tests — implemented.
- M2: fixed-period QF_NRA with explicit scope — implemented.
- M3: exact discounted/finite-horizon stochastic validators and stationary-profile
  QF_NRA campaigns with independent rational witness checking — implemented.
- M4: deterministic Rayon million-game screen and exact handoff — implemented.
- M5: rational model extraction, reproducible multi-solver artifacts, native proof
  retention, exact one-generator algebraic witnesses, automated Sturm root isolation
  and bisection, and independent Farkas / SMT-LIB2 proof checking — implemented.
  General multivariate algebraic models remain open.
- M6: finite symbolic AKRS paths and finite unions of exact rational V-polytopes for
  essential APS with exact Minkowski sums, support functions, subspace projections,
  and canonical Carathéodory hulls — implemented. Curved, irrational, and general
  semialgebraic set representations remain open.
- M7: Lean certificate lemmas and automated Lean 4 theorem export — implemented and
  formally proved with Mathlib under the pinned toolchain (3,139 jobs passing with zero sorry).
- M8: Enterprise Web Workbench with unified obsidian glassmorphism UI, 10 interactive suites,
  real-time API integration, and full system diagnostics — implemented. A paper is
  appropriate only after a genuinely new theorem or counterexample, independent reruns,
  and mathematical peer review.
