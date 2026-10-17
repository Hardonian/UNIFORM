from fractions import Fraction

from uniform_lab.elimination import (
    MultivariatePolynomial,
    eliminate_quitting_game,
    indifference_polynomials,
    prem,
    resultant,
)
from uniform_lab.io import load_quitting_game


def test_multivariate_polynomial_arithmetic() -> None:
    p0 = MultivariatePolynomial.var(0, 2)
    p1 = MultivariatePolynomial.var(1, 2)
    poly = (p0 + p1) * (p0 - p1)
    assert poly.degree(0) == 2
    assert poly.degree(1) == 2
    # p0^2 - p1^2: eval at p0=3, p1=2 => 9 - 4 = 5
    res = poly.evaluate({0: Fraction(3), 1: Fraction(2)})
    assert res.terms[(0, 0)] == Fraction(5)


def test_resultant_and_prem() -> None:
    # Res(a*x + b, c*x + d, x) = a*d - b*c
    # In variable 0: (2*x + 3) and (5*x + 7)
    p1 = MultivariatePolynomial.var(0, 1) * 2 + 3
    p2 = MultivariatePolynomial.var(0, 1) * 5 + 7
    res = resultant(p1, p2, 0)
    assert res.degree(0) == 0
    # 2*7 - 3*5 = 14 - 15 = -1; primitive scales to 1
    assert abs(res.terms[(0,)]) == Fraction(1)

    # Quadratic prem: (x^2 + 2x + 3) rem (x + 1) in variable 0
    q = MultivariatePolynomial.var(0, 1) ** 2 + MultivariatePolynomial.var(0, 1) * 2 + 3
    d = MultivariatePolynomial.var(0, 1) + 1
    r = prem(q, d, 0)
    assert r.degree(0) == 0
    # At x = -1, remainder is non-zero constant, which primitive scales to 1
    assert r.terms[(0,)] == Fraction(1)


def test_indifference_polynomials_two_player() -> None:
    game = load_quitting_game("examples/two_player_cycle.json")
    eqs = indifference_polynomials(game)
    assert len(eqs) == 2
    # In 2-player game, player 0's indifference condition depends only on player 1's action
    assert eqs[0].degree(0) == 0
    assert eqs[0].degree(1) >= 1
    assert eqs[1].degree(1) == 0
    assert eqs[1].degree(0) >= 1

    res = eliminate_quitting_game(game)
    assert res.stationary_equilibrium_possible
    assert res.interior_candidate_status == "confirmed"
    assert len(res.isolated_interior_roots) >= 1


def test_eliminate_three_player_mesh() -> None:
    game = load_quitting_game("examples/three_player_mesh.json")
    res = eliminate_quitting_game(game)
    assert res.players == 3
    assert res.characteristic_polynomial is not None
    assert res.characteristic_polynomial.degree == 12
    assert len(res.isolated_interior_roots) == 4
    assert res.stationary_equilibrium_possible is None
    assert res.interior_candidate_status == "eliminant_roots_found"


def test_eliminate_adversarial_candidate_46876() -> None:
    game = load_quitting_game("examples/adversarial_candidate_46876.json")
    res = eliminate_quitting_game(game)
    assert res.players == 4
    assert res.bivariate_degrees is not None
    # Verifies that it reduced to bivariate in (q0, q1) in milliseconds
    assert res.bivariate_degrees[0] > 0
    assert res.bivariate_degrees[1] > 0
    assert res.stationary_equilibrium_possible is None
    assert res.interior_candidate_status == "reduced_not_solved"
