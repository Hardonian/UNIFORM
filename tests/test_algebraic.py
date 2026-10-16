import json
from fractions import Fraction
from pathlib import Path

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


def test_exact_solan_vieille_algebraic_period_two_certificate() -> None:
    game = load_quitting_game(ROOT / "examples" / "solan_vieille_2002.json")
    data = json.loads(
        (
            ROOT
            / "examples"
            / "profiles"
            / "solan_vieille_period2_exact_algebraic.json"
        ).read_text(encoding="utf-8")
    )
    field, profile = load_algebraic_profile(game, data)
    certificate = certify_algebraic_profile(game, field, profile)
    assert certificate.exact_equilibrium_in_scope
    assert certificate.certificate.maximum_regret == 0
    payload = certificate.to_dict()
    assert payload["generator"]["root_count_in_open_interval"] == 1
    assert payload["exact_equilibrium_in_scope"] is True
