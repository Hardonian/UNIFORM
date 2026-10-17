from fractions import Fraction

import pytest

from uniform_lab.bivariate import (
    BivariateBox,
    BivariatePolynomial,
    RationalInterval,
    branch_and_prune_2d,
)


def test_rational_interval_operations() -> None:
    i1 = RationalInterval(Fraction(1, 2), Fraction(2))
    i2 = RationalInterval(Fraction(-1), Fraction(1))

    assert i1.width == Fraction(3, 2)
    assert i1.midpoint == Fraction(5, 4)
    assert not i1.contains_zero()
    assert i2.contains_zero()

    # Addition and Subtraction
    assert (i1 + i2) == RationalInterval(Fraction(-1, 2), Fraction(3))
    assert (i1 - i2) == RationalInterval(Fraction(-1, 2), Fraction(3))

    # Multiplication
    assert (i1 * i2) == RationalInterval(Fraction(-2), Fraction(2))

    # Powers
    assert i1.pow(2) == RationalInterval(Fraction(1, 4), Fraction(4))
    assert i2.pow(2) == RationalInterval(Fraction(0), Fraction(1))
    assert i2.pow(3) == RationalInterval(Fraction(-1), Fraction(1))


def test_rational_interval_invalid_construction() -> None:
    with pytest.raises(ValueError, match="cannot exceed hi"):
        RationalInterval(Fraction(2), Fraction(1))

    with pytest.raises(ValueError, match="Negative powers"):
        RationalInterval(Fraction(1), Fraction(2)).pow(-1)


def test_bivariate_box_bisection() -> None:
    box = BivariateBox(
        RationalInterval(Fraction(0), Fraction(1)),
        RationalInterval(Fraction(0), Fraction(1, 2)),
    )
    b1, b2 = box.bisect()
    assert b1.x == RationalInterval(Fraction(0), Fraction(1, 2))
    assert b2.x == RationalInterval(Fraction(1, 2), Fraction(1))
    assert b1.y == RationalInterval(Fraction(0), Fraction(1, 2))

    # Bisect along y when y is wider
    box_y = BivariateBox(
        RationalInterval(Fraction(0), Fraction(1, 4)),
        RationalInterval(Fraction(0), Fraction(1)),
    )
    by1, by2 = box_y.bisect()
    assert by1.y == RationalInterval(Fraction(0), Fraction(1, 2))
    assert by2.y == RationalInterval(Fraction(1, 2), Fraction(1))


def test_bivariate_polynomial_evaluation() -> None:
    # P(x, y) = x^2 + y - 1
    poly = BivariatePolynomial({(2, 0): Fraction(1), (0, 1): Fraction(1), (0, 0): Fraction(-1)})
    assert poly.max_deg_x == 2
    assert poly.max_deg_y == 1

    box = BivariateBox(
        RationalInterval(Fraction(0), Fraction(1)),
        RationalInterval(Fraction(0), Fraction(1)),
    )
    enc = poly.evaluate_box(box)
    assert enc.lo == Fraction(-1)
    assert enc.hi == Fraction(1)


def test_branch_and_prune_certifies_disjoint_systems() -> None:
    # P1(x, y) = x - 1/4
    # P2(x, y) = x - 3/4
    # Obviously have no common roots
    p1 = BivariatePolynomial({(1, 0): Fraction(1), (0, 0): Fraction(-1, 4)})
    p2 = BivariatePolynomial({(1, 0): Fraction(1), (0, 0): Fraction(-3, 4)})

    domain = BivariateBox(
        RationalInterval(Fraction(0), Fraction(1)),
        RationalInterval(Fraction(0), Fraction(1)),
    )

    cert = branch_and_prune_2d(p1, p2, domain)
    assert cert.certified_unsat is True
    assert cert.boxes_pruned > 0
    assert len(cert.unresolved_boxes) == 0

    doc = cert.to_dict()
    assert doc["schema"] == "uniform.bivariate-exclusion-certificate/v1"
    assert doc["certified_unsat"] is True


def test_branch_and_prune_detects_common_root() -> None:
    # P1(x, y) = x - 1/2
    # P2(x, y) = y - 1/2
    # Has common root at (1/2, 1/2)
    p1 = BivariatePolynomial({(1, 0): Fraction(1), (0, 0): Fraction(-1, 2)})
    p2 = BivariatePolynomial({(0, 1): Fraction(1), (0, 0): Fraction(-1, 2)})

    domain = BivariateBox(
        RationalInterval(Fraction(0), Fraction(1)),
        RationalInterval(Fraction(0), Fraction(1)),
    )

    cert = branch_and_prune_2d(p1, p2, domain, min_width=Fraction(1, 16))
    assert cert.certified_unsat is False
    assert len(cert.unresolved_boxes) > 0
    # Every unresolved box contains (1/2, 1/2)
    for b in cert.unresolved_boxes:
        assert b.x.contains(Fraction(1, 2))
        assert b.y.contains(Fraction(1, 2))

def test_extract_bivariate_resultants_and_prune() -> None:
    import json

    from uniform_lab.bivariate import extract_bivariate_resultants, prune_quitting_game
    from uniform_lab.quitting import QuittingGame

    with open("examples/adversarial_candidate_46876.json", encoding="utf-8") as f:
        game = QuittingGame.from_dict(json.load(f))

    p1, p2 = extract_bivariate_resultants(game)
    assert p1.max_deg_x >= 20
    assert p2.max_deg_x >= 20

    cert = prune_quitting_game(game, max_evaluations=15, min_width=Fraction(1, 4))
    assert cert.boxes_evaluated > 0
    assert cert.to_dict()["schema"] == "uniform.bivariate-exclusion-certificate/v1"

    # Non-4-player error check
    with open("examples/one_player_zero.json", encoding="utf-8") as f:
        game_1p = QuittingGame.from_dict(json.load(f))
    with pytest.raises(ValueError, match="require exactly 4 players"):
        extract_bivariate_resultants(game_1p)

