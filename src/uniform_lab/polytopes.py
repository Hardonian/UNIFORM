"""Exact rational V-polytopes for the essential APS operator.

The representation is a finite union of convex hulls.  Half-space clipping retains
all old feasible generators and all pairwise boundary intersections.  This may keep
redundant points, but its convex hull is exact and no continuum is discarded.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from .absorption import successor_graph
from .quitting import QuittingGame
from .rational import Q, rational_text

Point = tuple[Q, ...]


def _dot(left: Sequence[Q], right: Sequence[Q]) -> Q:
    return sum((a * b for a, b in zip(left, right, strict=True)), Fraction(0))


@dataclass(frozen=True)
class RationalPolytope:
    """The convex hull of a nonempty finite set of exact rational generators."""

    vertices: tuple[Point, ...]

    def __post_init__(self) -> None:
        if not self.vertices:
            raise ValueError("a polytope needs at least one generator")
        dimension = len(self.vertices[0])
        if dimension < 1 or any(len(point) != dimension for point in self.vertices):
            raise ValueError("polytope generators must have one common positive dimension")
        if any(not isinstance(value, Fraction) for point in self.vertices for value in point):
            raise TypeError("polytope coordinates must be Fractions")
        object.__setattr__(self, "vertices", tuple(sorted(set(self.vertices))))

    @property
    def dimension(self) -> int:
        return len(self.vertices[0])

    def clip_halfspace(self, normal: Sequence[Q], bound: Q) -> RationalPolytope | None:
        """Intersect with ``normal dot x <= bound`` using exact segment crossings."""

        if len(normal) != self.dimension:
            raise ValueError("half-space normal has the wrong dimension")
        offsets = tuple(_dot(normal, point) - bound for point in self.vertices)
        output = {
            point for point, offset in zip(self.vertices, offsets, strict=True) if offset <= 0
        }
        for left_index, left in enumerate(self.vertices):
            for right_index in range(left_index + 1, len(self.vertices)):
                right = self.vertices[right_index]
                left_offset, right_offset = offsets[left_index], offsets[right_index]
                if (left_offset < 0 < right_offset) or (right_offset < 0 < left_offset):
                    weight = -left_offset / (right_offset - left_offset)
                    output.add(
                        tuple(
                            left[axis] + weight * (right[axis] - left[axis])
                            for axis in range(self.dimension)
                        )
                    )
        return None if not output else RationalPolytope(tuple(output))

    def clip_hyperplane(self, normal: Sequence[Q], bound: Q) -> RationalPolytope | None:
        first = self.clip_halfspace(normal, bound)
        if first is None:
            return None
        return first.clip_halfspace(tuple(-value for value in normal), -bound)

    def nonnegative_part(self) -> RationalPolytope | None:
        result: RationalPolytope | None = self
        for axis in range(self.dimension):
            if result is None:
                return None
            normal = tuple(
                Fraction(-1) if index == axis else Fraction(0)
                for index in range(self.dimension)
            )
            result = result.clip_halfspace(normal, Fraction(0))
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "representation": "convex-hull-generators",
            "dimension": self.dimension,
            "vertices": [
                [rational_text(value) for value in point] for point in self.vertices
            ],
        }


@dataclass(frozen=True)
class PolytopeFamily:
    """A finite union of exact rational convex polytopes."""

    polytopes: tuple[RationalPolytope, ...] = ()

    def __post_init__(self) -> None:
        unique = {polytope.vertices: polytope for polytope in self.polytopes}
        object.__setattr__(
            self, "polytopes", tuple(unique[key] for key in sorted(unique))
        )

    def union(self, *others: PolytopeFamily) -> PolytopeFamily:
        return PolytopeFamily(
            self.polytopes + tuple(polytope for other in others for polytope in other.polytopes)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "representation": "finite-union-of-rational-v-polytopes",
            "polytopes": [polytope.to_dict() for polytope in self.polytopes],
        }


def t_i_polytope(
    game: QuittingGame, player: int, continuation: RationalPolytope
) -> RationalPolytope | None:
    if continuation.dimension != game.players:
        raise ValueError("continuation polytope has the wrong dimension")
    quit_row = game.payoffs[1 << player]
    hull = RationalPolytope((quit_row, *continuation.vertices))
    normal = tuple(
        Fraction(1) if axis == player else Fraction(0) for axis in range(game.players)
    )
    section = hull.clip_hyperplane(normal, Fraction(0))
    return None if section is None else section.nonnegative_part()


def t_i_family(
    game: QuittingGame, player: int, continuations: PolytopeFamily
) -> PolytopeFamily:
    output: list[RationalPolytope] = []
    for continuation in continuations.polytopes:
        image = t_i_polytope(game, player, continuation)
        if image is not None:
            output.append(image)
    return PolytopeFamily(tuple(output))


def essential_aps_polytopes(
    game: QuittingGame, sets: Mapping[int, PolytopeFamily]
) -> dict[int, PolytopeFamily]:
    """Apply the successor-restricted essential APS operator without dropping segments."""

    successors = successor_graph(game)
    result: dict[int, PolytopeFamily] = {}
    for player in range(game.players):
        continuation = PolytopeFamily(
            tuple(
                polytope
                for successor in successors[player]
                for polytope in sets.get(successor, PolytopeFamily()).polytopes
            )
        )
        images = t_i_family(game, player, continuation)
        quit_row = game.payoffs[1 << player]
        if all(value >= 0 for value in quit_row):
            images = images.union(PolytopeFamily((RationalPolytope((quit_row,)),)))
        result[player] = images
    return result


@dataclass(frozen=True)
class APSIteration:
    iterations: int
    fixed_point: bool
    sets: Mapping[int, PolytopeFamily]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "uniform.essential-aps-polytopes/v1",
            "iterations": self.iterations,
            "fixed_point": self.fixed_point,
            "equality": "exact equality of retained convex-hull generator representations",
            "sets": {str(player): family.to_dict() for player, family in self.sets.items()},
        }


def iterate_essential_aps(
    game: QuittingGame, initial: Mapping[int, PolytopeFamily], steps: int
) -> APSIteration:
    if steps < 0:
        raise ValueError("steps must be non-negative")
    current = {player: initial.get(player, PolytopeFamily()) for player in range(game.players)}
    for iteration in range(1, steps + 1):
        following = essential_aps_polytopes(game, current)
        if following == current:
            return APSIteration(iteration, True, following)
        current = following
    return APSIteration(steps, False, current)
