from fractions import Fraction

import pytest

from uniform_lab.rational import parse_rational, rational_text


def test_strict_rational_parser() -> None:
    assert parse_rational("-6/8") == Fraction(-3, 4)
    assert parse_rational(Fraction(2, 5)) == Fraction(2, 5)
    assert parse_rational(3) == 3
    assert rational_text(Fraction(6, 3)) == "2"
    with pytest.raises(TypeError, match="floating-point"):
        parse_rational(0.5)
    with pytest.raises(ValueError):
        parse_rational("0.5")
    with pytest.raises(TypeError):
        parse_rational(True)
