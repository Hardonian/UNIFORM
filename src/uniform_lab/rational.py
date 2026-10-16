"""Strict rational parsing and JSON conversion.

Floating-point input is deliberately rejected.  Exact certificates must not silently
inherit a binary rounding error from JSON.
"""

from __future__ import annotations

from fractions import Fraction
from typing import TypeAlias

Q: TypeAlias = Fraction


def parse_rational(value: object, *, field: str = "value") -> Q:
    """Parse a Fraction, integer, or ``a/b`` decimal-free string exactly."""

    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise TypeError(f"{field}: booleans are not rational numbers")
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        raise TypeError(f"{field}: floating-point JSON is forbidden; use a string fraction")
    if not isinstance(value, str):
        raise TypeError(f"{field}: expected integer or rational string, got {type(value).__name__}")
    text = value.strip()
    if not text or any(ch in text.lower() for ch in (".", "e")):
        raise ValueError(f"{field}: expected an integer or a/b, got {value!r}")
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{field}: invalid rational {value!r}") from exc


def rational_text(value: Q) -> str:
    """Return a stable, machine-readable representation."""

    return (
        str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
    )


def vector(values: object, *, length: int | None = None, field: str = "vector") -> tuple[Q, ...]:
    if not isinstance(values, list):
        raise TypeError(f"{field}: expected a JSON array")
    result = tuple(parse_rational(value, field=f"{field}[{i}]") for i, value in enumerate(values))
    if length is not None and len(result) != length:
        raise ValueError(f"{field}: expected {length} entries, got {len(result)}")
    return result
