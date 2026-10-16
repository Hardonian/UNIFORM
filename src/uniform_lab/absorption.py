"""Finite symbolic absorption paths and a point-set essential APS operator.

The path representation retains both continuous hazard intervals and discrete jumps.
It implements the exact constraints in AKRS Definition 4.3 and the sequential
perfectness checks in Definition 4.13 for this finitely represented subclass.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction

from .quitting import QuittingGame, outcome_probability
from .rational import Q


@dataclass(frozen=True)
class ContinuousHazard:
    start: Q
    end: Q
    density: Mapping[int, Q]


@dataclass(frozen=True)
class DiscreteJump:
    at: Q
    quit_probabilities: tuple[Q, ...]


PathPiece = ContinuousHazard | DiscreteJump


@dataclass(frozen=True)
class PathCheck:
    valid: bool
    errors: tuple[str, ...]
    endpoint: Q
    total_mass: tuple[Q, ...]


@dataclass(frozen=True)
class SequentialCheck:
    epsilon: Q
    valid: bool
    violations: tuple[str, ...]


def _is_singleton(mask: int) -> bool:
    return mask > 0 and mask & (mask - 1) == 0


class AbsorptionPath:
    """A finite concatenation of exact continuous hazards and product-form jumps."""

    def __init__(self, game: QuittingGame, pieces: Sequence[PathPiece]) -> None:
        self.game = game
        self.pieces = tuple(pieces)

    def check(self, *, require_absorbing: bool = True) -> PathCheck:
        cursor = Fraction(0)
        mass = [Fraction(0) for _ in range(1 << self.game.players)]
        errors: list[str] = []
        for index, piece in enumerate(self.pieces):
            if isinstance(piece, ContinuousHazard):
                if piece.start != cursor:
                    errors.append(
                        f"piece {index}: continuous start {piece.start} != cursor {cursor}"
                    )
                if not piece.start < piece.end <= 1:
                    errors.append(
                        f"piece {index}: continuous interval must satisfy start < end <= 1"
                    )
                if any(
                    not _is_singleton(mask) or mask >= (1 << self.game.players)
                    for mask in piece.density
                ):
                    errors.append(
                        f"piece {index}: continuous mass may use singleton quit masks only"
                    )
                if any(value < 0 for value in piece.density.values()):
                    errors.append(f"piece {index}: density must be non-negative")
                if sum(piece.density.values(), Fraction(0)) != 1:
                    errors.append(f"piece {index}: density must sum exactly to 1")
                width = piece.end - piece.start
                for mask, density in piece.density.items():
                    if 0 < mask < len(mass):
                        mass[mask] += width * density
                cursor = piece.end
            else:
                if piece.at != cursor:
                    errors.append(f"piece {index}: jump time {piece.at} != cursor {cursor}")
                if len(piece.quit_probabilities) != self.game.players:
                    errors.append(f"piece {index}: jump profile has the wrong dimension")
                    continue
                if any(value < 0 or value > 1 for value in piece.quit_probabilities):
                    errors.append(f"piece {index}: jump probabilities must lie in [0,1]")
                absorption = Fraction(0)
                for mask in range(1, 1 << self.game.players):
                    delta = (1 - cursor) * outcome_probability(piece.quit_probabilities, mask)
                    mass[mask] += delta
                    absorption += delta
                if absorption == 0:
                    errors.append(f"piece {index}: a discrete jump must have positive absorption")
                cursor += absorption
        if cursor > 1:
            errors.append(f"path endpoint {cursor} exceeds 1")
        if require_absorbing and cursor != 1:
            errors.append(f"absorbing path must end at 1, got {cursor}")
        if sum(mass, Fraction(0)) != cursor:
            errors.append("internal mass/parameter mismatch")
        return PathCheck(not errors, tuple(errors), cursor, tuple(mass))

    def _future_mass(self, piece_index: int, offset: Q = Fraction(0)) -> tuple[Q, ...]:
        """Mass strictly after a point inside a continuous piece or after a jump."""

        mass = [Fraction(0) for _ in range(1 << self.game.players)]
        piece = self.pieces[piece_index]
        if isinstance(piece, ContinuousHazard):
            remaining = piece.end - (piece.start + offset)
            for mask, density in piece.density.items():
                mass[mask] += remaining * density
        for future in self.pieces[piece_index + 1 :]:
            if isinstance(future, ContinuousHazard):
                for mask, density in future.density.items():
                    mass[mask] += (future.end - future.start) * density
            else:
                for mask in range(1, 1 << self.game.players):
                    mass[mask] += (1 - future.at) * outcome_probability(
                        future.quit_probabilities, mask
                    )
        return tuple(mass)

    def _payoff_from_mass(self, mass: Sequence[Q]) -> tuple[Q, ...]:
        total = sum(mass, Fraction(0))
        if total == 0:
            return tuple(Fraction(0) for _ in range(self.game.players))
        return tuple(
            sum(
                mass[mask] * self.game.payoffs[mask][player]
                for mask in range(1, 1 << self.game.players)
            )
            / total
            for player in range(self.game.players)
        )

    def payoff(self) -> tuple[Q, ...]:
        check = self.check()
        if not check.valid:
            raise ValueError("invalid absorption path: " + "; ".join(check.errors))
        return self._payoff_from_mass(check.total_mass)

    def sequential_epsilon_check(self, epsilon: Q = Fraction(0)) -> SequentialCheck:
        """Verify SP.1/SP.2 at all pieces using exact endpoint monotonicity.

        On a constant-density interval every payoff coordinate is a linear-fractional
        function with constant-sign derivative, so checking both endpoints checks the
        whole interval.
        """

        if epsilon < 0:
            raise ValueError("epsilon must be non-negative")
        structural = self.check()
        if not structural.valid:
            return SequentialCheck(epsilon, False, structural.errors)
        violations: list[str] = []
        for index, piece in enumerate(self.pieces):
            if isinstance(piece, ContinuousHazard):
                width = piece.end - piece.start
                probes = (Fraction(0), width) if piece.end < 1 else (Fraction(0),)
                for offset in probes:
                    gamma = self._payoff_from_mass(self._future_mass(index, offset))
                    for player in range(self.game.players):
                        singleton = self.game.payoffs[1 << player][player]
                        if gamma[player] < singleton - epsilon:
                            violations.append(
                                f"continuous piece {index}, player {player}: "
                                "quitting gain exceeds epsilon"
                            )
                        rate = piece.density.get(1 << player, Fraction(0))
                        if rate > 0 and gamma[player] > singleton + epsilon:
                            violations.append(
                                f"continuous piece {index}, player {player}: "
                                "active quitter is not indifferent"
                            )
            else:
                continuation = self._payoff_from_mass(self._future_mass(index))
                q = piece.quit_probabilities
                for player in range(self.game.players):
                    action_values: list[Q] = []
                    for action in (0, 1):
                        expected = Fraction(0)
                        for other_mask in range(1 << self.game.players):
                            if other_mask & (1 << player):
                                continue
                            probability = Fraction(1)
                            for other in range(self.game.players):
                                if other == player:
                                    continue
                                probability *= (
                                    q[other] if other_mask & (1 << other) else 1 - q[other]
                                )
                            mask = other_mask | (action << player)
                            payoff = (
                                continuation[player]
                                if mask == 0
                                else self.game.payoffs[mask][player]
                            )
                            expected += probability * payoff
                        action_values.append(expected)
                    mixed = (1 - q[player]) * action_values[0] + q[player] * action_values[1]
                    if max(action_values) > mixed + epsilon:
                        violations.append(
                            f"jump {index}, player {player}: profitable one-shot deviation"
                        )
                    for action in (0, 1):
                        support = (1 - q[player]) if action == 0 else q[player]
                        if support > 0 and mixed > action_values[action] + epsilon:
                            violations.append(
                                f"jump {index}, player {player}: supported action is more than "
                                "epsilon below value"
                            )
        return SequentialCheck(epsilon, not violations, tuple(violations))


def single_quit_matrix(game: QuittingGame) -> tuple[tuple[Q, ...], ...]:
    """Rows R_i = r(Q_i, C_-i), matching the 2026 paper's convention."""

    return tuple(game.payoffs[1 << player] for player in range(game.players))


def successor_graph(game: QuittingGame) -> tuple[tuple[int, ...], ...]:
    """Return S_i = {j: R[j,i] < 0 < R[i,j]} (2026 Eq. 5)."""

    matrix = single_quit_matrix(game)
    return tuple(
        tuple(
            successor
            for successor in range(game.players)
            if successor != player and matrix[successor][player] < 0 < matrix[player][successor]
        )
        for player in range(game.players)
    )


def strongly_connected_components(
    graph: Sequence[Sequence[int]],
) -> tuple[tuple[int, ...], ...]:
    """Tarjan components in deterministic topological discovery order."""

    index = 0
    indices: dict[int, int] = {}
    lowlinks: dict[int, int] = {}
    stack: list[int] = []
    on_stack: set[int] = set()
    components: list[tuple[int, ...]] = []

    def visit(vertex: int) -> None:
        nonlocal index
        indices[vertex] = lowlinks[vertex] = index
        index += 1
        stack.append(vertex)
        on_stack.add(vertex)
        for successor in graph[vertex]:
            if successor not in indices:
                visit(successor)
                lowlinks[vertex] = min(lowlinks[vertex], lowlinks[successor])
            elif successor in on_stack:
                lowlinks[vertex] = min(lowlinks[vertex], indices[successor])
        if lowlinks[vertex] == indices[vertex]:
            component: list[int] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == vertex:
                    break
            components.append(tuple(sorted(component)))

    for vertex in range(len(graph)):
        if vertex not in indices:
            visit(vertex)
    return tuple(components)


@dataclass(frozen=True)
class PointOperatorResult:
    points: tuple[tuple[Q, ...], ...]
    has_unrepresented_segments: bool


def t_i_points(
    game: QuittingGame, player: int, continuations: Sequence[Sequence[Q]]
) -> PointOperatorResult:
    """Exact T_i(E) for a finite point cloud E, flagging continuum-valued cases."""

    row = game.payoffs[1 << player]
    output: set[tuple[Q, ...]] = set()
    continuum = False
    if all(value >= 0 for value in row):
        output.add(row)
    for continuation_raw in continuations:
        continuation = tuple(continuation_raw)
        if len(continuation) != game.players:
            raise ValueError("continuation point has the wrong dimension")
        denominator = continuation[player] - row[player]
        if denominator == 0:
            if continuation[player] == 0:
                continuum = True
                for endpoint in (row, continuation):
                    if all(value >= 0 for value in endpoint):
                        output.add(endpoint)
            continue
        lam = continuation[player] / denominator
        if 0 <= lam <= 1:
            point = tuple(lam * row[i] + (1 - lam) * continuation[i] for i in range(game.players))
            if all(value >= 0 for value in point):
                output.add(point)
    return PointOperatorResult(tuple(sorted(output)), continuum)


def essential_aps_points(
    game: QuittingGame, sets: Mapping[int, Sequence[Sequence[Q]]]
) -> dict[int, PointOperatorResult]:
    """Finite-point version of F_{N,i}: use only successor-indexed continuations."""

    successors = successor_graph(game)
    result: dict[int, PointOperatorResult] = {}
    for player in range(game.players):
        continuation_points = [point for j in successors[player] for point in sets.get(j, ())]
        result[player] = t_i_points(game, player, continuation_points)
    return result
