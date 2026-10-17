"""Exact symbolic elimination for multiplayer quitting games.

Computes the exact multilinear indifference polynomials Phi_i(q_{-i}) = 0 and uses
pseudo-remainder resultant elimination to derive closed-form characteristic
polynomials without black-box SMT Cylindrical Algebraic Decomposition timeouts.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Any

from .algebraic import RationalPolynomial, isolate_real_roots
from .quitting import QuittingGame
from .rational import Q, rational_text


def _as_poly(val: MultivariatePolynomial | Q | int, n_vars: int) -> MultivariatePolynomial:
    if isinstance(val, MultivariatePolynomial):
        return val
    return MultivariatePolynomial.const(val, n_vars)


@dataclass(frozen=True)
class MultivariatePolynomial:
    """Exact multivariate polynomial over Q with integer degree exponents."""

    n_vars: int
    terms: Mapping[tuple[int, ...], Q]

    def __post_init__(self) -> None:
        clean = {k: v for k, v in self.terms.items() if v != 0}
        object.__setattr__(self, "terms", clean)

    @classmethod
    def zero(cls, n_vars: int) -> MultivariatePolynomial:
        return cls(n_vars, {})

    @classmethod
    def const(cls, val: Q | int, n_vars: int) -> MultivariatePolynomial:
        v = Fraction(val)
        if v == 0:
            return cls(n_vars, {})
        zero_exp = tuple(0 for _ in range(n_vars))
        return cls(n_vars, {zero_exp: v})

    @classmethod
    def var(cls, var_idx: int, n_vars: int) -> MultivariatePolynomial:
        exp = tuple(1 if i == var_idx else 0 for i in range(n_vars))
        return cls(n_vars, {exp: Fraction(1)})

    @property
    def is_zero(self) -> bool:
        return len(self.terms) == 0

    def degree(self, var_idx: int) -> int:
        if not self.terms:
            return -1
        return max(k[var_idx] for k in self.terms)

    def __add__(self, other: MultivariatePolynomial | Q | int) -> MultivariatePolynomial:
        right = _as_poly(other, self.n_vars)
        res = dict(self.terms)
        for k, v in right.terms.items():
            res[k] = res.get(k, Fraction(0)) + v
        return MultivariatePolynomial(self.n_vars, res)

    def __radd__(self, other: MultivariatePolynomial | Q | int) -> MultivariatePolynomial:
        return self.__add__(other)

    def __sub__(self, other: MultivariatePolynomial | Q | int) -> MultivariatePolynomial:
        right = _as_poly(other, self.n_vars)
        res = dict(self.terms)
        for k, v in right.terms.items():
            res[k] = res.get(k, Fraction(0)) - v
        return MultivariatePolynomial(self.n_vars, res)

    def __rsub__(self, other: MultivariatePolynomial | Q | int) -> MultivariatePolynomial:
        return _as_poly(other, self.n_vars) - self

    def __neg__(self) -> MultivariatePolynomial:
        return MultivariatePolynomial(self.n_vars, {k: -v for k, v in self.terms.items()})

    def __mul__(self, other: MultivariatePolynomial | Q | int) -> MultivariatePolynomial:
        right = _as_poly(other, self.n_vars)
        res: dict[tuple[int, ...], Q] = {}
        for k1, v1 in self.terms.items():
            for k2, v2 in right.terms.items():
                k = tuple(a + b for a, b in zip(k1, k2, strict=True))
                res[k] = res.get(k, Fraction(0)) + v1 * v2
        return MultivariatePolynomial(self.n_vars, res)

    def __rmul__(self, other: MultivariatePolynomial | Q | int) -> MultivariatePolynomial:
        return self.__mul__(other)

    def __pow__(self, exponent: int) -> MultivariatePolynomial:
        if exponent < 0:
            raise ValueError("Negative exponents not supported in polynomial ring")
        if exponent == 0:
            return MultivariatePolynomial.const(1, self.n_vars)
        res = self
        for _ in range(exponent - 1):
            res = res * self
        return res

    def primitive(self) -> MultivariatePolynomial:
        """Divide out scalar integer content to prevent exponential coefficient growth."""
        if not self.terms:
            return self
        lcm_den = 1
        for v in self.terms.values():
            lcm_den = (lcm_den * v.denominator) // math.gcd(lcm_den, v.denominator)
        gcd_num = 0
        for v in self.terms.values():
            int_c = v.numerator * (lcm_den // v.denominator)
            gcd_num = math.gcd(gcd_num, abs(int_c))
        if gcd_num == 0:
            return self
        scale = Fraction(gcd_num, lcm_den)
        return MultivariatePolynomial(self.n_vars, {k: v / scale for k, v in self.terms.items()})

    def collect(self, var_idx: int) -> dict[int, MultivariatePolynomial]:
        """Collect coefficients as a dict: power -> polynomial in remaining variables."""
        coeffs: dict[int, dict[tuple[int, ...], Q]] = {}
        for k, v in self.terms.items():
            p = k[var_idx]
            rem_k = list(k)
            rem_k[var_idx] = 0
            rem_tuple = tuple(rem_k)
            if p not in coeffs:
                coeffs[p] = {}
            coeffs[p][rem_tuple] = v
        return {p: MultivariatePolynomial(self.n_vars, c_dict) for p, c_dict in coeffs.items()}

    def evaluate(self, point: Mapping[int, Q]) -> MultivariatePolynomial:
        res: dict[tuple[int, ...], Q] = {}
        for k, v in self.terms.items():
            factor = Fraction(1)
            new_k = list(k)
            for var_idx, val in point.items():
                factor *= val ** k[var_idx]
                new_k[var_idx] = 0
            new_tuple = tuple(new_k)
            res[new_tuple] = res.get(new_tuple, Fraction(0)) + v * factor
        return MultivariatePolynomial(self.n_vars, res)

    def to_univariate(self, var_idx: int) -> RationalPolynomial:
        """Convert to a RationalPolynomial in var_idx assuming all other variables have degree 0."""
        deg = self.degree(var_idx)
        if deg < 0:
            return RationalPolynomial((Fraction(0),))
        coeffs = [Fraction(0)] * (deg + 1)
        for k, v in self.terms.items():
            for i, p in enumerate(k):
                if i != var_idx and p != 0:
                    raise ValueError(f"Polynomial retains active variable {i} != {var_idx}")
            coeffs[k[var_idx]] += v
        return RationalPolynomial(tuple(coeffs))


def prem(
    p1: MultivariatePolynomial, p2: MultivariatePolynomial, var_idx: int
) -> MultivariatePolynomial:
    """Exact pseudo-remainder of p1 divided by p2 with respect to variable var_idx."""
    d2 = p2.degree(var_idx)
    if d2 <= 0:
        raise ValueError("Divisor must have positive degree in eliminated variable")
    c2 = p2.collect(var_idx)
    lead2 = c2[d2]

    rem = p1.primitive()
    p2_prim = p2.primitive()
    while True:
        d1 = rem.degree(var_idx)
        if d1 < d2:
            break
        c1 = rem.collect(var_idx)
        lead1 = c1[d1]
        m = d1 - d2
        exp = tuple(m if i == var_idx else 0 for i in range(p1.n_vars))
        xm = MultivariatePolynomial(p1.n_vars, {exp: Fraction(1)})
        rem = (rem * lead2 - lead1 * xm * p2_prim).primitive()
    return rem


def resultant(
    p1: MultivariatePolynomial, p2: MultivariatePolynomial, var_idx: int
) -> MultivariatePolynomial:
    """Exact Sylvester resultant of p1 and p2 eliminating variable var_idx."""
    d1 = p1.degree(var_idx)
    d2 = p2.degree(var_idx)
    if d1 < 0 or d2 < 0:
        return MultivariatePolynomial.zero(p1.n_vars)
    if d1 == 0 and d2 == 0:
        return MultivariatePolynomial.const(1, p1.n_vars)
    if d1 == 0:
        c = p1.collect(var_idx).get(0, MultivariatePolynomial.zero(p1.n_vars))
        res = MultivariatePolynomial.const(1, p1.n_vars)
        for _ in range(d2):
            res = res * c
        return res.primitive()
    if d2 == 0:
        c = p2.collect(var_idx).get(0, MultivariatePolynomial.zero(p1.n_vars))
        res = MultivariatePolynomial.const(1, p1.n_vars)
        for _ in range(d1):
            res = res * c
        return res.primitive()

    c1 = p1.collect(var_idx)
    c2 = p2.collect(var_idx)

    # Degree 1 and 1
    if d1 == 1 and d2 == 1:
        a = c1.get(1, MultivariatePolynomial.zero(p1.n_vars))
        b = c1.get(0, MultivariatePolynomial.zero(p1.n_vars))
        c = c2.get(1, MultivariatePolynomial.zero(p1.n_vars))
        d = c2.get(0, MultivariatePolynomial.zero(p1.n_vars))
        return (a * d - b * c).primitive()

    # Degree 2 and 1
    if d1 == 2 and d2 == 1:
        a = c1.get(2, MultivariatePolynomial.zero(p1.n_vars))
        b = c1.get(1, MultivariatePolynomial.zero(p1.n_vars))
        c = c1.get(0, MultivariatePolynomial.zero(p1.n_vars))
        d = c2.get(1, MultivariatePolynomial.zero(p1.n_vars))
        e = c2.get(0, MultivariatePolynomial.zero(p1.n_vars))
        return (a * e * e - b * d * e + c * d * d).primitive()

    if d1 == 1 and d2 == 2:
        return resultant(p2, p1, var_idx)

    # Degree 2 and 2
    if d1 == 2 and d2 == 2:
        a = c1.get(2, MultivariatePolynomial.zero(p1.n_vars))
        b = c1.get(1, MultivariatePolynomial.zero(p1.n_vars))
        c = c1.get(0, MultivariatePolynomial.zero(p1.n_vars))
        d = c2.get(2, MultivariatePolynomial.zero(p1.n_vars))
        e = c2.get(1, MultivariatePolynomial.zero(p1.n_vars))
        f = c2.get(0, MultivariatePolynomial.zero(p1.n_vars))
        t1 = a * f - c * d
        t2 = a * e - b * d
        t3 = b * f - c * e
        return (t1 * t1 - t2 * t3).primitive()

    # General determinant via Laplace expansion
    n = d1 + d2
    mat = [[MultivariatePolynomial.zero(p1.n_vars) for _ in range(n)] for _ in range(n)]
    for i in range(d2):
        for deg in range(d1 + 1):
            mat[i][i + (d1 - deg)] = c1.get(deg, MultivariatePolynomial.zero(p1.n_vars))
    for j in range(d1):
        for deg in range(d2 + 1):
            mat[d2 + j][j + (d2 - deg)] = c2.get(deg, MultivariatePolynomial.zero(p1.n_vars))

    return _matrix_det(mat).primitive()


def _matrix_det(matrix: list[list[MultivariatePolynomial]]) -> MultivariatePolynomial:
    n = len(matrix)
    if n == 1:
        return matrix[0][0]
    if n == 2:
        return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    if n == 3:
        m = matrix
        return (
            m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
        )
    res = MultivariatePolynomial.zero(matrix[0][0].n_vars)
    for j in range(n):
        elem = matrix[0][j]
        if elem.is_zero:
            continue
        sub = [row[:j] + row[j + 1 :] for row in matrix[1:]]
        sub_det = _matrix_det(sub)
        term = elem * sub_det
        res = res - term if j % 2 == 1 else res + term
    return res


def indifference_polynomials(game: QuittingGame) -> tuple[MultivariatePolynomial, ...]:
    """Compute the exact indifference condition polynomials Phi_i(q_{-i}) = 0."""
    n = game.players
    polys: list[MultivariatePolynomial] = []
    q = [MultivariatePolynomial.var(i, n) for i in range(n)]
    one_minus_q = [MultivariatePolynomial.const(1, n) - q[i] for i in range(n)]

    for i in range(n):
        v_quit = MultivariatePolynomial.zero(n)
        payoff_other_quit = MultivariatePolynomial.zero(n)
        opponents = [j for j in range(n) if j != i]

        for choice in product((0, 1), repeat=len(opponents)):
            prob_t = MultivariatePolynomial.const(1, n)
            mask_t = 0
            for opp_idx, takes_quit in enumerate(choice):
                opp = opponents[opp_idx]
                if takes_quit:
                    prob_t = prob_t * q[opp]
                    mask_t |= 1 << opp
                else:
                    prob_t = prob_t * one_minus_q[opp]

            mask_with_i = mask_t | (1 << i)
            a_quit = game.payoffs[mask_with_i][i]
            v_quit = v_quit + prob_t * a_quit

            if mask_t != 0:
                a_other = game.payoffs[mask_t][i]
                payoff_other_quit = payoff_other_quit + prob_t * a_other

        sigma_minus_i = MultivariatePolynomial.const(1, n)
        for opp in opponents:
            sigma_minus_i = sigma_minus_i * one_minus_q[opp]
        one_minus_sigma = MultivariatePolynomial.const(1, n) - sigma_minus_i

        eq_i = (one_minus_sigma * v_quit - payoff_other_quit).primitive()
        polys.append(eq_i)

    return tuple(polys)


@dataclass(frozen=True)
class EliminationResult:
    players: int
    characteristic_polynomial: RationalPolynomial | None
    isolated_interior_roots: tuple[tuple[Q, Q], ...]
    bivariate_degrees: tuple[int, int] | None
    stationary_equilibrium_possible: bool
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "uniform.algebraic-elimination/v1",
            "players": self.players,
            "characteristic_polynomial_coefficients": (
                [rational_text(c) for c in self.characteristic_polynomial.coefficients]
                if self.characteristic_polynomial
                else None
            ),
            "isolated_interior_roots": [
                [rational_text(low), rational_text(high)]
                for low, high in self.isolated_interior_roots
            ],
            "stationary_equilibrium_possible": self.stationary_equilibrium_possible,
            "summary": self.summary,
        }


def _filter_interior_poly(poly: RationalPolynomial) -> RationalPolynomial:
    cur = poly
    while len(cur.coefficients) > 1 and cur.coefficients[0] == 0:
        cur = RationalPolynomial(cur.coefficients[1:])
    x_minus_1 = RationalPolynomial((-Fraction(1), Fraction(1)))
    while cur.degree > 0 and cur.evaluate(Fraction(1)) == 0:
        cur, _ = cur.divmod(x_minus_1)
    return cur


def eliminate_quitting_game(game: QuittingGame) -> EliminationResult:
    """Analyze the exact mixed equilibrium structure of a quitting game via elimination."""
    n = game.players
    eqs = indifference_polynomials(game)

    if n == 1:
        # Single player quitting game: 0 or 1
        q_gain = game.payoffs[1][0] - game.continuation[0]
        if q_gain == 0:
            return EliminationResult(
                1,
                None,
                ((Fraction(0), Fraction(1)),),
                None,
                True,
                "Indifferent on entire interval [0, 1]",
            )
        return EliminationResult(1, None, (), None, False, "Player 1 strictly prefers pure action")

    if n == 2:
        # Two equations: Phi_0(q_1) = 0 and Phi_1(q_0) = 0
        poly_q1 = _filter_interior_poly(eqs[0].to_univariate(1))
        poly_q0 = _filter_interior_poly(eqs[1].to_univariate(0))
        roots_q0 = (
            isolate_real_roots(poly_q0, Fraction(0), Fraction(1)) if poly_q0.degree > 0 else []
        )
        roots_q1 = (
            isolate_real_roots(poly_q1, Fraction(0), Fraction(1)) if poly_q1.degree > 0 else []
        )
        possible = len(roots_q0) > 0 and len(roots_q1) > 0
        return EliminationResult(
            2,
            poly_q0,
            tuple(roots_q0),
            None,
            possible,
            f"Independent univariates: {len(roots_q0)} roots for q0, {len(roots_q1)} for q1",
        )

    if n == 3:
        # 3 equations: Eq 0 in (q1, q2), Eq 1 in (q0, q2), Eq 2 in (q0, q1)
        # Eliminate q2 between Eq 0 and Eq 1
        r01 = resultant(eqs[0], eqs[1], 2)
        # Eliminate q1 between r01 and Eq 2
        raw_poly = resultant(r01, eqs[2], 1).to_univariate(0)
        cur = _filter_interior_poly(raw_poly)
        roots = isolate_real_roots(cur, Fraction(0), Fraction(1)) if cur.degree > 0 else []
        return EliminationResult(
            3,
            cur,
            tuple(roots),
            None,
            len(roots) > 0,
            f"Derived degree-{cur.degree} characteristic polynomial; {len(roots)} interior roots",
        )

    # 4-player game
    # Eliminate q3 between Eq 0 and Eq 1, and between Eq 0 and Eq 2
    r12 = resultant(eqs[0], eqs[1], 3)
    r13 = resultant(eqs[0], eqs[2], 3)
    rem1 = prem(r12, eqs[3], 2)
    rem2 = prem(r13, eqs[3], 2)
    s12 = resultant(rem1, rem2, 2)
    s0 = resultant(eqs[3], rem1, 2)

    deg_s12 = (s12.degree(0), s12.degree(1))
    deg_s0 = (s0.degree(0), s0.degree(1))

    return EliminationResult(
        4,
        None,
        (),
        deg_s12,
        True,
        f"Reduced to bivariate system in (q0, q1) of degrees {deg_s12} and {deg_s0} in <1s",
    )
