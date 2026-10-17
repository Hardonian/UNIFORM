"""Exact rational 2D bivariate interval arithmetic and branch-and-prune root exclusion engine.

This engine certifies that two bivariate polynomials P1(x, y) = 0 and P2(x, y) = 0
have NO simultaneous real zeros anywhere in a rational box [a, b] x [c, d].
All operations strictly adhere to the UNIFORM zero-float exact arithmetic guarantee.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Mapping


@dataclass(frozen=True)
class RationalInterval:
    """Exact closed rational interval [lo, hi]."""

    lo: Fraction
    hi: Fraction

    def __post_init__(self) -> None:
        if self.lo > self.hi:
            raise ValueError(f"Invalid interval: lo ({self.lo}) cannot exceed hi ({self.hi})")

    def contains(self, val: Fraction) -> bool:
        return self.lo <= val <= self.hi

    def contains_zero(self) -> bool:
        return self.lo <= 0 <= self.hi

    @property
    def width(self) -> Fraction:
        return self.hi - self.lo

    @property
    def midpoint(self) -> Fraction:
        return (self.lo + self.hi) / 2

    def __add__(self, other: RationalInterval) -> RationalInterval:
        return RationalInterval(self.lo + other.lo, self.hi + other.hi)

    def __sub__(self, other: RationalInterval) -> RationalInterval:
        return RationalInterval(self.lo - other.hi, self.hi - other.lo)

    def __mul__(self, other: RationalInterval) -> RationalInterval:
        p1 = self.lo * other.lo
        p2 = self.lo * other.hi
        p3 = self.hi * other.lo
        p4 = self.hi * other.hi
        return RationalInterval(min(p1, p2, p3, p4), max(p1, p2, p3, p4))

    def scale(self, c: Fraction) -> RationalInterval:
        if c >= 0:
            return RationalInterval(self.lo * c, self.hi * c)
        return RationalInterval(self.hi * c, self.lo * c)

    def pow(self, n: int) -> RationalInterval:
        if n < 0:
            raise ValueError("Negative powers are not supported for polynomial interval evaluation")
        if n == 0:
            return RationalInterval(Fraction(1), Fraction(1))
        if n % 2 == 1:
            return RationalInterval(self.lo**n, self.hi**n)
        if self.lo >= 0:
            return RationalInterval(self.lo**n, self.hi**n)
        if self.hi <= 0:
            return RationalInterval(self.hi**n, self.lo**n)
        return RationalInterval(Fraction(0), max(self.lo**n, self.hi**n))


@dataclass(frozen=True)
class BivariateBox:
    """A 2D rational bounding box [x_lo, x_hi] x [y_lo, y_hi]."""

    x: RationalInterval
    y: RationalInterval

    def bisect(self) -> tuple[BivariateBox, BivariateBox]:
        """Bisect the box along its coordinate axis of greatest width."""
        if self.x.width >= self.y.width:
            mid = self.x.midpoint
            return (
                BivariateBox(RationalInterval(self.x.lo, mid), self.y),
                BivariateBox(RationalInterval(mid, self.x.hi), self.y),
            )
        mid = self.y.midpoint
        return (
            BivariateBox(self.x, RationalInterval(self.y.lo, mid)),
            BivariateBox(self.x, RationalInterval(mid, self.y.hi)),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "x": [str(self.x.lo), str(self.x.hi)],
            "y": [str(self.y.lo), str(self.y.hi)],
            "max_width": str(max(self.x.width, self.y.width)),
        }


@dataclass(frozen=True)
class BivariatePolynomial:
    """A 2D polynomial with exact rational coefficients: sum c_(i, j) * x^i * y^j."""

    terms: Mapping[tuple[int, int], Fraction]

    @property
    def max_deg_x(self) -> int:
        return max((i for i, _ in self.terms), default=0)

    @property
    def max_deg_y(self) -> int:
        return max((j for _, j in self.terms), default=0)

    def evaluate_box(self, box: BivariateBox) -> RationalInterval:
        """Evaluate exact interval enclosure over a 2D box."""
        if not self.terms:
            return RationalInterval(Fraction(0), Fraction(0))

        # Precompute interval powers
        x_pows: dict[int, RationalInterval] = {}
        for i in range(self.max_deg_x + 1):
            x_pows[i] = box.x.pow(i)

        y_pows: dict[int, RationalInterval] = {}
        for j in range(self.max_deg_y + 1):
            y_pows[j] = box.y.pow(j)

        acc_lo = Fraction(0)
        acc_hi = Fraction(0)

        for (i, j), coeff in self.terms.items():
            if coeff == 0:
                continue
            term_interval = (x_pows[i] * y_pows[j]).scale(coeff)
            acc_lo += term_interval.lo
            acc_hi += term_interval.hi

        return RationalInterval(acc_lo, acc_hi)


@dataclass(frozen=True)
class BivariateExclusionCertificate:
    """Exact certificate of simultaneous zero exclusion over a 2D rational domain."""

    certified_unsat: bool
    domain: BivariateBox
    boxes_evaluated: int
    boxes_pruned: int
    unresolved_boxes: tuple[BivariateBox, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "uniform.bivariate-exclusion-certificate/v1",
            "certified_unsat": self.certified_unsat,
            "domain": self.domain.to_dict(),
            "boxes_evaluated": self.boxes_evaluated,
            "boxes_pruned": self.boxes_pruned,
            "unresolved_count": len(self.unresolved_boxes),
            "unresolved_boxes": [b.to_dict() for b in self.unresolved_boxes[:10]],
        }


def branch_and_prune_2d(
    p1: BivariatePolynomial,
    p2: BivariatePolynomial,
    domain: BivariateBox,
    *,
    max_evaluations: int = 10000,
    min_width: Fraction = Fraction(1, 2**12),
) -> BivariateExclusionCertificate:
    """Branch-and-prune recursive box subdivision to certify simultaneous root exclusion.

    If both 0 in box(p1) and 0 in box(p2), the box cannot be immediately pruned.
    Boxes are recursively bisected until either pruned or min_width is reached.
    """
    queue = [domain]
    evaluated = 0
    pruned = 0
    unresolved: list[BivariateBox] = []

    while queue and evaluated < max_evaluations:
        box = queue.pop()
        evaluated += 1

        enc1 = p1.evaluate_box(box)
        if not enc1.contains_zero():
            pruned += 1
            continue

        enc2 = p2.evaluate_box(box)
        if not enc2.contains_zero():
            pruned += 1
            continue

        # Both contain zero
        if max(box.x.width, box.y.width) <= min_width:
            unresolved.append(box)
            continue

        b1, b2 = box.bisect()
        queue.append(b1)
        queue.append(b2)

    certified = len(unresolved) == 0 and len(queue) == 0
    return BivariateExclusionCertificate(
        certified_unsat=certified,
        domain=domain,
        boxes_evaluated=evaluated,
        boxes_pruned=pruned,
        unresolved_boxes=tuple(unresolved),
    )
