import json
from fractions import Fraction
from pathlib import Path

import pytest

from uniform_lab.algebraic import (
    AlgebraicField,
    RationalPolynomial,
    certify_algebraic_profile,
    load_algebraic_profile,
    roots_in_open_interval,
)
from uniform_lab.io import load_quitting_game

ROOT = Path(__file__).parents[1]


def test_sturm_isolation_and_exact_field_arithmetic() -> None:
    polynomial = RationalPolynomial.from_values([-2, 0, 1])
    assert roots_in_open_interval(polynomial, Fraction(1), Fraction(2)) == 1
    field = AlgebraicField(polynomial, Fraction(1), Fraction(2), "a")
    a = field.generator
    assert a * a == 2
    assert 1 < a < 2
    assert (a + 1) / (a + 1) == 1


def test_root_interval_rejects_multiple_roots_and_endpoint_roots() -> None:
    polynomial = RationalPolynomial.from_values([-1, 0, 1])
    with pytest.raises(ValueError, match="exactly one root"):
        AlgebraicField(polynomial, Fraction(-2), Fraction(2))
    with pytest.raises(ValueError, match="endpoints"):
        AlgebraicField(polynomial, Fraction(1), Fraction(2))


def test_exact_solan_vieille_algebraic_period_two_certificate() -> None:
    game = load_quitting_game(ROOT / "examples" / "solan_vieille_2002.json")
    data = json.loads(
        (ROOT / "examples" / "profiles" / "solan_vieille_period2_exact_algebraic.json").read_text(
            encoding="utf-8"
        )
    )
    field, profile = load_algebraic_profile(game, data)
    certificate = certify_algebraic_profile(game, field, profile)
    assert certificate.exact_equilibrium_in_scope
    payload = certificate.to_dict()
    assert payload["generator"]["root_count_in_open_interval"] == 1
    assert payload["exact_equilibrium_in_scope"] is True


def test_isolate_real_roots_and_decimal_approx() -> None:
    # x^2 - 2 = 0 has roots -sqrt(2) and +sqrt(2)
    poly = RationalPolynomial.from_values([-2, 0, 1])
    from uniform_lab.algebraic import isolate_real_roots

    intervals = isolate_real_roots(poly)
    assert len(intervals) == 2
    assert intervals[0][0] < -1 < intervals[0][1]
    assert intervals[1][0] < 1 < intervals[1][1]

    # Construct field from root index 1 (+sqrt(2))
    field = AlgebraicField.from_root_index(poly, root_index=1, symbol="sqrt2")
    elem = field.generator
    approx = elem.to_decimal_approx(decimals=6)
    assert approx.startswith("1.41421")
