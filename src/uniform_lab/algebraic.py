"""Exact certificates over a real algebraic generator.

An element is represented by a rational polynomial in ``alpha``, reduced modulo a
defining polynomial.  The selected real root is fixed by a rational isolating
interval.  Comparisons use Sturm root counts and interval refinement; no floating
point approximation participates in a certificate.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import zip_longest
from typing import Any, cast

from .quitting import PeriodicRegretCertificate, QuittingGame, periodic_regret_certificate
from .rational import Q, parse_rational, rational_text


def _trim(values: Sequence[Q]) -> tuple[Q, ...]:
    result = list(values)
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return tuple(result) if result else (Fraction(0),)


@dataclass(frozen=True)
class RationalPolynomial:
    """A univariate polynomial with coefficients in ascending degree order."""

    coefficients: tuple[Q, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "coefficients", _trim(self.coefficients))
        if not all(isinstance(value, Fraction) for value in self.coefficients):
            raise TypeError("polynomial coefficients must be Fractions")

    @classmethod
    def from_values(cls, values: Sequence[object]) -> RationalPolynomial:
        if not values:
            raise ValueError("a polynomial needs at least one coefficient")
        return cls(tuple(parse_rational(value, field="coefficient") for value in values))

    @property
    def degree(self) -> int:
        return -1 if self.is_zero else len(self.coefficients) - 1

    @property
    def is_zero(self) -> bool:
        return self.coefficients == (Fraction(0),)

    @property
    def leading(self) -> Q:
        return self.coefficients[-1]

    def evaluate(self, value: Q) -> Q:
        result = Fraction(0)
        for coefficient in reversed(self.coefficients):
            result = result * value + coefficient
        return result

    def derivative(self) -> RationalPolynomial:
        if self.degree <= 0:
            return RationalPolynomial((Fraction(0),))
        return RationalPolynomial(
            tuple(index * value for index, value in enumerate(self.coefficients[1:], 1))
        )

    def monic(self) -> RationalPolynomial:
        if self.is_zero:
            return self
        return self / self.leading

    def __neg__(self) -> RationalPolynomial:
        return RationalPolynomial(tuple(-value for value in self.coefficients))

    def __add__(self, other: RationalPolynomial | Q | int) -> RationalPolynomial:
        right = _as_polynomial(other)
        return RationalPolynomial(
            tuple(
                a + b
                for a, b in zip_longest(
                    self.coefficients, right.coefficients, fillvalue=Fraction(0)
                )
            )
        )

    __radd__ = __add__

    def __sub__(self, other: RationalPolynomial | Q | int) -> RationalPolynomial:
        return self + -_as_polynomial(other)

    def __rsub__(self, other: RationalPolynomial | Q | int) -> RationalPolynomial:
        return _as_polynomial(other) - self

    def __mul__(self, other: RationalPolynomial | Q | int) -> RationalPolynomial:
        right = _as_polynomial(other)
        output = [Fraction(0)] * (len(self.coefficients) + len(right.coefficients) - 1)
        for i, left_value in enumerate(self.coefficients):
            for j, right_value in enumerate(right.coefficients):
                output[i + j] += left_value * right_value
        return RationalPolynomial(tuple(output))

    __rmul__ = __mul__

    def __truediv__(self, scalar: Q | int) -> RationalPolynomial:
        divisor = Fraction(scalar)
        if divisor == 0:
            raise ZeroDivisionError("polynomial division by zero")
        return RationalPolynomial(tuple(value / divisor for value in self.coefficients))

    def divmod(self, divisor: RationalPolynomial) -> tuple[RationalPolynomial, RationalPolynomial]:
        if divisor.is_zero:
            raise ZeroDivisionError("polynomial division by zero")
        remainder = list(self.coefficients)
        quotient = [Fraction(0)] * max(1, self.degree - divisor.degree + 1)
        while not (len(remainder) == 1 and remainder[0] == 0) and len(remainder) >= len(
            divisor.coefficients
        ):
            shift = len(remainder) - len(divisor.coefficients)
            scale = remainder[-1] / divisor.leading
            quotient[shift] = scale
            for index, value in enumerate(divisor.coefficients):
                remainder[index + shift] -= scale * value
            remainder = list(_trim(remainder))
        return RationalPolynomial(tuple(quotient)), RationalPolynomial(tuple(remainder))

    def __mod__(self, divisor: RationalPolynomial) -> RationalPolynomial:
        return self.divmod(divisor)[1]

    def to_list(self) -> list[str]:
        return [rational_text(value) for value in self.coefficients]


def _as_polynomial(value: RationalPolynomial | Q | int) -> RationalPolynomial:
    if isinstance(value, RationalPolynomial):
        return value
    return RationalPolynomial((Fraction(value),))


def polynomial_gcd(left: RationalPolynomial, right: RationalPolynomial) -> RationalPolynomial:
    while not right.is_zero:
        left, right = right, left % right
    return left.monic()


def _extended_gcd(
    left: RationalPolynomial, right: RationalPolynomial
) -> tuple[RationalPolynomial, RationalPolynomial, RationalPolynomial]:
    old_r, r = left, right
    old_s, s = _as_polynomial(1), _as_polynomial(0)
    old_t, t = _as_polynomial(0), _as_polynomial(1)
    while not r.is_zero:
        quotient, remainder = old_r.divmod(r)
        old_r, r = r, remainder
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
    scale = old_r.leading
    return old_r / scale, old_s / scale, old_t / scale


def sturm_sequence(polynomial: RationalPolynomial) -> tuple[RationalPolynomial, ...]:
    if polynomial.degree < 1:
        raise ValueError("Sturm sequences require a nonconstant polynomial")
    sequence = [polynomial.monic(), polynomial.derivative()]
    while not sequence[-1].is_zero:
        remainder = sequence[-2] % sequence[-1]
        if remainder.is_zero:
            break
        sequence.append(-remainder)
    return tuple(sequence)


def _sign(value: Q) -> int:
    return (value > 0) - (value < 0)


def _variations(sequence: Sequence[RationalPolynomial], at: Q) -> int:
    signs = [_sign(polynomial.evaluate(at)) for polynomial in sequence]
    nonzero = [value for value in signs if value]
    return sum(a != b for a, b in zip(nonzero, nonzero[1:], strict=False))


def roots_in_open_interval(polynomial: RationalPolynomial, lower: Q, upper: Q) -> int:
    if lower >= upper:
        raise ValueError("root interval must have lower < upper")
    if polynomial.evaluate(lower) == 0 or polynomial.evaluate(upper) == 0:
        raise ValueError("root interval endpoints must not be roots")
    sequence = sturm_sequence(polynomial)
    return _variations(sequence, lower) - _variations(sequence, upper)


def _interval_multiply(left: tuple[Q, Q], right: tuple[Q, Q]) -> tuple[Q, Q]:
    candidates = (
        left[0] * right[0],
        left[0] * right[1],
        left[1] * right[0],
        left[1] * right[1],
    )
    return min(candidates), max(candidates)


def polynomial_interval(polynomial: RationalPolynomial, lower: Q, upper: Q) -> tuple[Q, Q]:
    result = (Fraction(0), Fraction(0))
    variable = (lower, upper)
    for coefficient in reversed(polynomial.coefficients):
        product = _interval_multiply(result, variable)
        result = (product[0] + coefficient, product[1] + coefficient)
    return result


def isolate_real_roots(
    polynomial: RationalPolynomial,
    lower: Q | None = None,
    upper: Q | None = None,
) -> list[tuple[Q, Q]]:
    """Isolate all real roots of a square-free polynomial into disjoint open intervals.

    Returns intervals sorted in ascending numerical order.
    """
    gcd = polynomial_gcd(polynomial, polynomial.derivative())
    sqfree = polynomial.divmod(gcd)[0]
    poly = sqfree.monic()
    if lower is None or upper is None:
        leading = abs(poly.leading)
        max_coeff = max((abs(c) for c in poly.coefficients[:-1]), default=Fraction(0))
        bound = Fraction(1) + max_coeff / leading
        # Add buffer to ensure endpoints are not roots
        while poly.evaluate(-bound) == 0:
            bound += 1
        while poly.evaluate(bound) == 0:
            bound += 1
        if lower is None:
            lower = -bound
        if upper is None:
            upper = bound

    # Subdivide intervals recursively
    intervals: list[tuple[Q, Q]] = []
    stack = [(lower, upper)]
    while stack:
        a, b = stack.pop()
        count = roots_in_open_interval(poly, a, b)
        if count == 0:
            continue
        if count == 1:
            intervals.append((a, b))
            continue
        mid = (a + b) / 2
        # Ensure midpoint is not a root
        offset = (b - a) / 8
        trial = 0
        while poly.evaluate(mid) == 0 and trial < 7:
            trial += 1
            mid = a + (trial * offset)
        if poly.evaluate(mid) == 0:
            # mid is an exact root! Isolate mid with a small delta
            delta = (b - a) / 16
            intervals.append((mid - delta, mid + delta))
            stack.append((mid + delta, b))
            stack.append((a, mid - delta))
        else:
            stack.append((mid, b))
            stack.append((a, mid))

    intervals.sort(key=lambda item: (item[0] + item[1]) / 2)
    return intervals


@dataclass(frozen=True)
class AlgebraicField:
    """A selected real root and exact arithmetic in its polynomial quotient."""

    polynomial: RationalPolynomial
    lower: Q
    upper: Q
    symbol: str = "alpha"

    def __post_init__(self) -> None:
        if self.polynomial.degree < 1:
            raise ValueError("defining polynomial must be nonconstant")
        if polynomial_gcd(self.polynomial, self.polynomial.derivative()).degree != 0:
            raise ValueError("defining polynomial must be square-free")
        count = roots_in_open_interval(self.polynomial, self.lower, self.upper)
        if count != 1:
            raise ValueError(f"isolating interval must contain exactly one root, found {count}")

    def element(self, coefficients: Sequence[object] | RationalPolynomial | Q | int) -> Algebraic:
        if isinstance(coefficients, RationalPolynomial):
            polynomial = coefficients
        elif isinstance(coefficients, (int, Fraction)):
            polynomial = _as_polynomial(coefficients)
        else:
            polynomial = RationalPolynomial.from_values(coefficients)
        return Algebraic(self, polynomial % self.polynomial)

    @property
    def generator(self) -> Algebraic:
        return self.element((0, 1))

    def sign(self, polynomial: RationalPolynomial) -> int:
        remainder = polynomial % self.polynomial
        if remainder.is_zero:
            return 0
        common = polynomial_gcd(self.polynomial, remainder)
        if common.degree > 0 and roots_in_open_interval(common, self.lower, self.upper) == 1:
            return 0
        lower, upper = self.lower, self.upper
        for _ in range(4096):
            image = polynomial_interval(remainder, lower, upper)
            if image[0] > 0:
                return 1
            if image[1] < 0:
                return -1
            midpoint = (lower + upper) / 2
            root_value = self.polynomial.evaluate(midpoint)
            if root_value == 0:
                return _sign(remainder.evaluate(midpoint))
            left_count = roots_in_open_interval(self.polynomial, lower, midpoint)
            if left_count == 1:
                upper = midpoint
            else:
                lower = midpoint
        raise ArithmeticError("could not decide algebraic sign after 4096 refinements")

    def refine_interval(self, max_width: Q) -> tuple[Q, Q]:
        """Refine the isolating interval until its width is strictly less than max_width."""
        lower, upper = self.lower, self.upper
        while (upper - lower) >= max_width:
            midpoint = (lower + upper) / 2
            if self.polynomial.evaluate(midpoint) == 0:
                # Midpoint is an exact rational root; nudge bounds symmetrically
                delta = (upper - lower) / 8
                return midpoint - delta, midpoint + delta
            if roots_in_open_interval(self.polynomial, lower, midpoint) == 1:
                upper = midpoint
            else:
                lower = midpoint
        return lower, upper

    @classmethod
    def from_root_index(
        cls,
        polynomial: RationalPolynomial,
        root_index: int = 0,
        symbol: str = "alpha",
    ) -> AlgebraicField:
        """Construct an AlgebraicField by isolating the i-th real root in ascending order."""
        intervals = isolate_real_roots(polynomial)
        if not intervals:
            raise ValueError("polynomial has no real roots")
        if not 0 <= root_index < len(intervals):
            msg = f"root index {root_index} out of range (found {len(intervals)} real roots)"
            raise IndexError(msg)
        lower, upper = intervals[root_index]
        return cls(polynomial.monic(), lower, upper, symbol=symbol)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "defining_polynomial_coefficients": self.polynomial.to_list(),
            "coefficient_order": "ascending",
            "isolating_interval": [rational_text(self.lower), rational_text(self.upper)],
            "root_count_in_open_interval": 1,
            "sign_algorithm": "Sturm root count, polynomial gcd, rational interval refinement",
        }


@dataclass(frozen=True)
class Algebraic:
    field: AlgebraicField
    polynomial: RationalPolynomial

    def _coerce(self, other: Algebraic | Q | int) -> Algebraic:
        if isinstance(other, Algebraic):
            if other.field != self.field:
                raise ValueError("cannot mix different algebraic generators")
            return other
        return self.field.element(other)

    def __add__(self, other: Algebraic | Q | int) -> Algebraic:
        right = self._coerce(other)
        return self.field.element(self.polynomial + right.polynomial)

    __radd__ = __add__

    def __neg__(self) -> Algebraic:
        return self.field.element(-self.polynomial)

    def __sub__(self, other: Algebraic | Q | int) -> Algebraic:
        return self + -self._coerce(other)

    def __rsub__(self, other: Algebraic | Q | int) -> Algebraic:
        return self._coerce(other) - self

    def __mul__(self, other: Algebraic | Q | int) -> Algebraic:
        right = self._coerce(other)
        return self.field.element(self.polynomial * right.polynomial)

    __rmul__ = __mul__

    def inverse(self) -> Algebraic:
        if self == 0:
            raise ZeroDivisionError("algebraic division by zero")
        gcd, coefficient, _ = _extended_gcd(self.polynomial, self.field.polynomial)
        if gcd.degree != 0:
            raise ZeroDivisionError("element is not invertible modulo the defining polynomial")
        return self.field.element(coefficient)

    def __truediv__(self, other: Algebraic | Q | int) -> Algebraic:
        return self * self._coerce(other).inverse()

    def __rtruediv__(self, other: Algebraic | Q | int) -> Algebraic:
        return self._coerce(other) / self

    def sign(self) -> int:
        return self.field.sign(self.polynomial)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (Algebraic, int, Fraction)):
            return False
        try:
            return (self - other).sign() == 0
        except ValueError:
            return False

    def __lt__(self, other: Algebraic | Q | int) -> bool:
        return (self - self._coerce(other)).sign() < 0

    def __le__(self, other: Algebraic | Q | int) -> bool:
        return (self - self._coerce(other)).sign() <= 0

    def __gt__(self, other: Algebraic | Q | int) -> bool:
        return (self - self._coerce(other)).sign() > 0

    def __ge__(self, other: Algebraic | Q | int) -> bool:
        return (self - self._coerce(other)).sign() >= 0

    def __hash__(self) -> int:
        return hash((self.field, self.polynomial))

    def to_float(self) -> float:
        """Return a floating-point approximation by interval midpoint evaluation."""
        midpoint = (self.field.lower + self.field.upper) / 2
        return float(self.polynomial.evaluate(midpoint))

    def to_decimal_approx(self, decimals: int = 15) -> str:
        """Return a verified decimal approximation string."""
        max_width = Fraction(1, 10 ** (decimals + 3))
        lower, upper = self.field.refine_interval(max_width)
        midpoint = (lower + upper) / 2
        val = float(self.polynomial.evaluate(midpoint))
        return f"{val:.{decimals}f}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "basis": [
                "1",
                *[
                    f"{self.field.symbol}^{power}"
                    for power in range(1, len(self.polynomial.coefficients))
                ],
            ],
            "coefficients": self.polynomial.to_list(),
            "sign": self.sign(),
            "decimal_approx": self.to_decimal_approx(decimals=14),
        }


AlgebraicProfile = tuple[tuple[Algebraic, ...], ...]


@dataclass(frozen=True)
class AlgebraicPeriodicCertificate:
    field: AlgebraicField
    profile: AlgebraicProfile
    certificate: PeriodicRegretCertificate

    @property
    def exact_equilibrium_in_scope(self) -> bool:
        maximum = cast(Algebraic, self.certificate.maximum_regret)
        return maximum.sign() <= 0

    def to_dict(self) -> dict[str, Any]:
        def matrix(values: Sequence[Sequence[Any]]) -> list[list[dict[str, Any]]]:
            return [[cast(Algebraic, value).to_dict() for value in row] for row in values]

        maximum = cast(Algebraic, self.certificate.maximum_regret)
        return {
            "schema": "uniform.algebraic-periodic-certificate/v1",
            "scope": self.certificate.scope,
            "arithmetic": "exact rational polynomial quotient with Sturm sign decisions",
            "generator": self.field.to_dict(),
            "profile": matrix(self.profile),
            "values_by_start_phase": matrix(self.certificate.values),
            "best_deviation_values_by_start_phase": matrix(self.certificate.best_deviation_values),
            "regrets_by_start_phase": matrix(self.certificate.regrets),
            "maximum_regret": maximum.to_dict(),
            "exact_equilibrium_in_scope": self.exact_equilibrium_in_scope,
            "maximizing_policies": [
                [list(policy) for policy in per_player]
                for per_player in self.certificate.maximizing_policies
            ],
        }


def load_algebraic_profile(
    game: QuittingGame, data: Mapping[str, Any]
) -> tuple[AlgebraicField, AlgebraicProfile]:
    if data.get("schema") != "uniform.algebraic-periodic-profile/v1":
        raise ValueError("unsupported algebraic periodic profile schema")
    generator = data.get("generator")
    if not isinstance(generator, Mapping):
        raise TypeError("generator must be an object")
    coefficients = generator.get("defining_polynomial_coefficients")
    interval = generator.get("isolating_interval")
    if not isinstance(coefficients, list) or not isinstance(interval, list) or len(interval) != 2:
        raise TypeError("generator needs coefficient array and two-element isolating interval")
    field = AlgebraicField(
        RationalPolynomial.from_values(coefficients),
        parse_rational(interval[0], field="generator.isolating_interval[0]"),
        parse_rational(interval[1], field="generator.isolating_interval[1]"),
        str(generator.get("symbol", "alpha")),
    )
    raw_profile = data.get("profile")
    if not isinstance(raw_profile, list) or not raw_profile:
        raise TypeError("profile must be a nonempty array")
    profile: list[tuple[Algebraic, ...]] = []
    for phase_index, raw_phase in enumerate(raw_profile):
        if not isinstance(raw_phase, list) or len(raw_phase) != game.players:
            raise ValueError(f"profile[{phase_index}] has the wrong player dimension")
        phase: list[Algebraic] = []
        for player, raw_element in enumerate(raw_phase):
            if not isinstance(raw_element, list):
                raise TypeError(f"profile[{phase_index}][{player}] must be a coefficient array")
            element = field.element(raw_element)
            if not 0 <= element <= 1:
                raise ValueError(f"profile[{phase_index}][{player}] is outside [0,1]")
            phase.append(element)
        profile.append(tuple(phase))
    return field, tuple(profile)


def certify_algebraic_profile(
    game: QuittingGame, field: AlgebraicField, profile: AlgebraicProfile
) -> AlgebraicPeriodicCertificate:
    if not profile or any(len(phase) != game.players for phase in profile):
        raise ValueError("algebraic profile has invalid dimensions")
    if any(value.field != field for phase in profile for value in phase):
        raise ValueError("profile contains a different algebraic generator")
    # The exact quitting engine is generic at runtime: Algebraic supplies the same
    # field operations and exact ordering as Fraction.
    certificate = periodic_regret_certificate(game, cast(Any, profile))
    return AlgebraicPeriodicCertificate(field, profile, certificate)
