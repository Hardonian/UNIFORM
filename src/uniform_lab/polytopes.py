"""Exact rational V-polytopes for the essential APS operator.

The representation is a finite union of convex hulls.  Half-space clipping retains
all old feasible generators and all pairwise boundary intersections.  Exact rational
convex-hull membership removes redundant generators, so fixed-point comparisons do
not depend on incidental interior points.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from typing import Any

from .absorption import successor_graph
from .quitting import QuittingGame
from .rational import Q, rational_text

Point = tuple[Q, ...]


def _dot(left: Sequence[Q], right: Sequence[Q]) -> Q:
    return sum((a * b for a, b in zip(left, right, strict=True)), Fraction(0))


def _full_column_rank_solution(
    matrix: Sequence[Sequence[Q]], rhs: Sequence[Q]
) -> tuple[Q, ...] | None:
    """Solve an overdetermined rational system when its columns are independent."""

    if len(matrix) != len(rhs) or not matrix:
        raise ValueError("invalid linear system dimensions")
    variables = len(matrix[0])
    if any(len(row) != variables for row in matrix):
        raise ValueError("ragged linear system")
    augmented = [list(row) + [value] for row, value in zip(matrix, rhs, strict=True)]
    pivot_row = 0
    pivot_rows: list[int] = []
    for column in range(variables):
        pivot = next(
            (row for row in range(pivot_row, len(augmented)) if augmented[row][column]),
            None,
        )
        if pivot is None:
            return None
        augmented[pivot_row], augmented[pivot] = augmented[pivot], augmented[pivot_row]
        scale = augmented[pivot_row][column]
        augmented[pivot_row] = [value / scale for value in augmented[pivot_row]]
        for row in range(len(augmented)):
            if row == pivot_row:
                continue
            scale = augmented[row][column]
            if scale:
                augmented[row] = [
                    augmented[row][entry] - scale * augmented[pivot_row][entry]
                    for entry in range(variables + 1)
                ]
        pivot_rows.append(pivot_row)
        pivot_row += 1
    if any(
        all(row[column] == 0 for column in range(variables)) and row[-1] != 0 for row in augmented
    ):
        return None
    return tuple(augmented[row][-1] for row in pivot_rows)


def point_in_convex_hull(point: Point, vertices: Sequence[Point]) -> bool:
    """Decide rational convex-hull membership exactly using Carathéodory simplices."""

    if not vertices:
        return False
    dimension = len(point)
    if any(len(vertex) != dimension for vertex in vertices):
        raise ValueError("convex-hull dimension mismatch")
    unique = tuple(sorted(set(vertices)))
    for size in range(1, min(dimension + 1, len(unique)) + 1):
        for simplex in combinations(unique, size):
            matrix = [
                [simplex[column][axis] for column in range(size)] for axis in range(dimension)
            ]
            matrix.append([Fraction(1)] * size)
            solution = _full_column_rank_solution(matrix, (*point, Fraction(1)))
            if solution is not None and all(weight >= 0 for weight in solution):
                return True
    return False


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
        unique = tuple(sorted(set(self.vertices)))
        extreme = tuple(
            point
            for point in unique
            if not point_in_convex_hull(point, tuple(other for other in unique if other != point))
        )
        object.__setattr__(self, "vertices", extreme)

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
                Fraction(-1) if index == axis else Fraction(0) for index in range(self.dimension)
            )
            result = result.clip_halfspace(normal, Fraction(0))
        return result

    def contains_point(self, point: Point) -> bool:
        """Decide exact membership in this convex polytope."""
        return point_in_convex_hull(point, self.vertices)

    def support_function(self, direction: Sequence[Q]) -> tuple[Q, Point]:
        """Compute the exact support function h_P(u) = max_{v in V} u dot v and an argmax vertex."""
        if len(direction) != self.dimension:
            raise ValueError("direction vector dimension mismatch")
        best_val: Q | None = None
        best_vertex: Point | None = None
        for v in self.vertices:
            val = _dot(direction, v)
            if best_val is None or val > best_val:
                best_val = val
                best_vertex = v
        assert best_val is not None and best_vertex is not None
        return best_val, best_vertex

    def minkowski_sum(self, other: RationalPolytope) -> RationalPolytope:
        """Compute the exact Minkowski sum P + Q = conv({u + v : u in P, v in Q})."""
        if self.dimension != other.dimension:
            raise ValueError("Minkowski sum requires matching dimensions")
        sum_vertices = [
            tuple(a + b for a, b in zip(u, v, strict=True))
            for u in self.vertices
            for v in other.vertices
        ]
        return RationalPolytope(tuple(sum_vertices))

    def project(self, axes: Sequence[int]) -> RationalPolytope:
        """Project onto a subset of coordinate axes."""
        if not axes:
            raise ValueError("axes must be non-empty")
        if any(not 0 <= ax < self.dimension for ax in axes):
            raise IndexError("axis index out of range")
        projected = [tuple(v[ax] for ax in axes) for v in self.vertices]
        return RationalPolytope(tuple(projected))

    def center_of_mass(self) -> Point:
        """Compute the arithmetic mean of extreme vertices."""
        n = Fraction(len(self.vertices))
        return tuple(
            sum((v[i] for v in self.vertices), Fraction(0)) / n for i in range(self.dimension)
        )

    def h_representation_2d(self) -> list[tuple[Point, Q]]:
        """Compute exact halfspace inequalities normal dot x <= bound for a 2D polytope."""
        if self.dimension != 2:
            raise ValueError("h_representation_2d requires dimension 2")
        if len(self.vertices) < 3:
            return []
        cx, cy = self.center_of_mass()
        # Sort vertices counter-clockwise
        import math

        sorted_verts = sorted(
            self.vertices,
            key=lambda v: math.atan2(float(v[1] - cy), float(v[0] - cx)),
        )
        inequalities: list[tuple[Point, Q]] = []
        for i in range(len(sorted_verts)):
            p1 = sorted_verts[i]
            p2 = sorted_verts[(i + 1) % len(sorted_verts)]
            # Outward normal for CCW edge: (dy, -dx)
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            normal: Point = (dy, -dx)
            bound = _dot(normal, p1)
            # Verify centroid is on the inner side (normal dot c <= bound)
            if _dot(normal, (cx, cy)) > bound:
                normal = (-normal[0], -normal[1])
                bound = -bound
            inequalities.append((normal, bound))
        return inequalities

    def to_dict(self) -> dict[str, Any]:
        return {
            "representation": "convex-hull-generators",
            "dimension": self.dimension,
            "vertices": [[rational_text(value) for value in point] for point in self.vertices],
            "center_of_mass": [rational_text(value) for value in self.center_of_mass()],
        }


@dataclass(frozen=True)
class PolytopeFamily:
    """A finite union of exact rational convex polytopes."""

    polytopes: tuple[RationalPolytope, ...] = ()

    def __post_init__(self) -> None:
        unique = {polytope.vertices: polytope for polytope in self.polytopes}
        ordered = tuple(unique[key] for key in sorted(unique))
        maximal = tuple(
            polytope
            for polytope in ordered
            if not any(
                polytope != other
                and all(
                    point_in_convex_hull(vertex, other.vertices) for vertex in polytope.vertices
                )
                for other in ordered
            )
        )
        object.__setattr__(self, "polytopes", maximal)

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
    normal = tuple(Fraction(1) if axis == player else Fraction(0) for axis in range(game.players))
    section = hull.clip_hyperplane(normal, Fraction(0))
    return None if section is None else section.nonnegative_part()


def t_i_family(game: QuittingGame, player: int, continuations: PolytopeFamily) -> PolytopeFamily:
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
            "equality": "exact equality of canonical rational extreme-point representations",
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
