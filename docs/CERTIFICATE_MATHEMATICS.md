# Certificate mathematics and trust boundary

## Quitting-game model

There are `n` players. At each nonabsorbing stage player `i` independently quits with
probability `q_i`. A nonzero bit mask `S` is the set of quitters and has terminal payoff
`r(S)`. Mask zero continues. If absorption never occurs, payoff is `g`.

For phase `t` of a period-`p` profile, let

```
s_t = product_i (1-q[t,i])
b_t = sum_(S != empty) Pr_t(S) r(S).
```

The conditional values are the unique cyclic solution

```
v_t = b_t + s_t v_(t+1 mod p)
```

when `product_t s_t < 1`. The implementation evaluates the equivalent geometric sum
with `fractions.Fraction`. If the product is one, every quitting probability is zero
and the value is defined to be `g`.

## Periodic regret certificate

For each player, every binary policy in `{continue, quit}^p` is substituted while the
opponents' independent periodic probabilities remain fixed. The same cyclic equations
are solved exactly, from every starting phase. Randomization cannot beat the best pure
policy in this finite phase-state control problem.

The emitted maximum is therefore valid for the strategy class printed in the
certificate: deterministic unilateral policies with the stated phase period. This
implementation deliberately does not turn that bounded result into a claim about
arbitrary nonperiodic behavioral profiles. A solver `UNSAT` result has exactly the same
restriction.

## Finite-horizon certificate

The terminal vector at horizon zero is `g`. Backward recursion applies the profile
expectation for its value and maximizes over the deviator's two current actions for the
best response. Thus every history-compatible action sequence through that horizon is
covered. The reported evaluation is the absorption payoff if absorption occurs by the
boundary, and `g` otherwise; it is not silently relabelled as another finite-average
convention.

## QF_NRA export

The exporter declares exact real probability and value variables. It asserts the
cyclic value equations for the profile and for every pure same-period deviation. A
zero absorption denominator is handled in a separate branch whose value is `g`, so no
division-by-zero convention is delegated to a solver. SAT rational models are parsed
and rechecked by the Python exact engine. Algebraic expressions that are not rational
are retained as unverified text; they are never rounded and promoted to certificates.

Solver SAT means “a candidate exists in the encoded class.” Solver UNSAT means only
“no candidate exists in the encoded class,” and is not a formal proof unless an
independently checkable proof trace is also retained.

## Absorption paths

The finite symbolic representation concatenates:

- continuous intervals whose total absorption parameter advances at unit speed and
  whose density is supported only on singleton quit masks; and
- discrete product-form jumps at parameter `t`, adding
  `(1-t) * product_i q_i^(a_i) (1-q_i)^(1-a_i)` for every nonzero action mask.

Structural validation enforces the AKRS conditions corresponding to total mass,
plateaus across jumps, product-form jump increments, and the absence of simultaneous
quitting mass in continuous time. Sequential checks implement SP.1 at jumps and SP.2
on continuous pieces. With constant density, each conditional payoff coordinate is a
linear-fractional function with constant-sign derivative, so exact endpoint checks
cover the complete interval.

The point-cloud essential APS operator implements

```
S_i = {j : R[j,i] < 0 < R[i,j]}
F_i(E) = ({R_i} if nonnegative) union T_i(union_(j in S_i) E_j).
```

When both endpoints already lie in player `i`'s zero-payoff hyperplane, `T_i` contains
a full segment. The implementation returns its endpoints and sets
`has_unrepresented_segments=true`; point iteration must not be presented as the full
set-valued operator in that case.

## General stochastic games

For a fixed stationary profile, the normalized discounted value solves

```
(I - beta P) v = (1-beta) r
```

by exact Gaussian elimination. Stationary regret enumerates all deterministic
stationary policies for one player. Finite-horizon regret uses full backward induction
and therefore permits time-dependent Markov deviations over that finite horizon.

## Trusted components

The trusted computing base for exact certificates is CPython integer arithmetic,
`fractions.Fraction`, the small algorithms in `src/uniform_lab`, the parsed game, and
the test suite. Rust output is screening evidence only until re-read by Python. Z3,
cvc5, numerical optimizers, and language models are candidate generators, not trusted
proof oracles. Lean files, when built, reduce the trusted theorem layer to Lean's kernel
and the stated Mathlib imports; unavailable build logs must be reported as unavailable.

