"""Exact validators for small finite multiplayer stochastic games."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from itertools import product

from .rational import Q

JointAction = tuple[int, ...]
StationaryProfile = tuple[tuple[tuple[Q, ...], ...], ...]


def solve_linear(matrix: Sequence[Sequence[Q]], rhs: Sequence[Q]) -> tuple[Q, ...]:
    n = len(rhs)
    augmented = [list(matrix[row]) + [rhs[row]] for row in range(n)]
    if any(len(row) != n + 1 for row in augmented):
        raise ValueError("linear system must be square")
    for column in range(n):
        pivot = next((row for row in range(column, n) if augmented[row][column] != 0), None)
        if pivot is None:
            raise ValueError("singular linear system")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [entry / scale for entry in augmented[column]]
        for row in range(n):
            if row == column:
                continue
            scale = augmented[row][column]
            if scale:
                augmented[row] = [
                    augmented[row][entry] - scale * augmented[column][entry]
                    for entry in range(n + 1)
                ]
    return tuple(augmented[row][-1] for row in range(n))


@dataclass(frozen=True)
class StochasticGame:
    states: int
    action_counts: tuple[int, ...]
    payoffs: Mapping[tuple[int, JointAction], tuple[Q, ...]]
    transitions: Mapping[tuple[int, JointAction], tuple[Q, ...]]

    def __post_init__(self) -> None:
        if (
            self.states < 1
            or not self.action_counts
            or any(count < 1 for count in self.action_counts)
        ):
            raise ValueError("states and action counts must be positive")
        players = len(self.action_counts)
        joints = tuple(product(*(range(count) for count in self.action_counts)))
        expected = {(state, joint) for state in range(self.states) for joint in joints}
        if set(self.payoffs) != expected or set(self.transitions) != expected:
            raise ValueError("payoffs and transitions must cover every state/joint action")
        for key in expected:
            if len(self.payoffs[key]) != players:
                raise ValueError(f"{key}: payoff dimension mismatch")
            transition = self.transitions[key]
            if len(transition) != self.states or any(value < 0 for value in transition):
                raise ValueError(f"{key}: invalid transition row")
            if sum(transition, Fraction(0)) != 1:
                raise ValueError(f"{key}: transition row must sum exactly to one")

    @property
    def players(self) -> int:
        return len(self.action_counts)

    def validate_profile(self, profile: StationaryProfile) -> None:
        if len(profile) != self.states:
            raise ValueError("profile state dimension mismatch")
        for state, state_profile in enumerate(profile):
            if len(state_profile) != self.players:
                raise ValueError(f"state {state}: player dimension mismatch")
            for player, probabilities in enumerate(state_profile):
                if len(probabilities) != self.action_counts[player]:
                    raise ValueError(f"state {state}, player {player}: action dimension mismatch")
                if (
                    any(value < 0 for value in probabilities)
                    or sum(probabilities, Fraction(0)) != 1
                ):
                    raise ValueError(
                        f"state {state}, player {player}: probabilities must sum to one"
                    )

    def induced(self, profile: StationaryProfile, player: int) -> tuple[list[Q], list[list[Q]]]:
        self.validate_profile(profile)
        rewards = [Fraction(0) for _ in range(self.states)]
        transition = [[Fraction(0) for _ in range(self.states)] for _ in range(self.states)]
        for state in range(self.states):
            for joint in product(*(range(count) for count in self.action_counts)):
                probability = Fraction(1)
                for other, action in enumerate(joint):
                    probability *= profile[state][other][action]
                key = (state, joint)
                rewards[state] += probability * self.payoffs[key][player]
                for target in range(self.states):
                    transition[state][target] += probability * self.transitions[key][target]
        return rewards, transition

    def discounted_values(self, profile: StationaryProfile, beta: Q) -> tuple[tuple[Q, ...], ...]:
        """Normalized discounted values: (1-beta) sum beta^t r_t."""

        if not 0 <= beta < 1:
            raise ValueError("beta must lie in [0,1)")
        by_player: list[tuple[Q, ...]] = []
        for player in range(self.players):
            rewards, transition = self.induced(profile, player)
            matrix = [
                [
                    Fraction(row == column) - beta * transition[row][column]
                    for column in range(self.states)
                ]
                for row in range(self.states)
            ]
            by_player.append(solve_linear(matrix, [(1 - beta) * value for value in rewards]))
        return tuple(
            tuple(by_player[player][state] for player in range(self.players))
            for state in range(self.states)
        )

    def _replace_policy(
        self, profile: StationaryProfile, player: int, policy: Sequence[int]
    ) -> StationaryProfile:
        result: list[tuple[tuple[Q, ...], ...]] = []
        for state, state_profile in enumerate(profile):
            players = list(state_profile)
            players[player] = tuple(
                Fraction(action == policy[state]) for action in range(self.action_counts[player])
            )
            result.append(tuple(players))
        return tuple(result)

    def discounted_stationary_regret(
        self, profile: StationaryProfile, beta: Q
    ) -> tuple[tuple[Q, ...], ...]:
        values = self.discounted_values(profile, beta)
        best = [
            [values[state][player] for player in range(self.players)]
            for state in range(self.states)
        ]
        for player in range(self.players):
            for policy in product(range(self.action_counts[player]), repeat=self.states):
                candidate = self.discounted_values(
                    self._replace_policy(profile, player, policy), beta
                )
                for state in range(self.states):
                    best[state][player] = max(best[state][player], candidate[state][player])
        return tuple(
            tuple(best[state][player] - values[state][player] for player in range(self.players))
            for state in range(self.states)
        )

    def finite_horizon_regret(
        self, profile: StationaryProfile, horizon: int
    ) -> tuple[tuple[Q, ...], ...]:
        """Regret for the normalized H-stage average payoff, at every initial state."""

        if horizon < 1:
            raise ValueError("horizon must be positive")
        self.validate_profile(profile)
        profile_total = [[Fraction(0) for _ in range(self.states)] for _ in range(self.players)]
        best_total = [[Fraction(0) for _ in range(self.states)] for _ in range(self.players)]
        for _ in range(horizon):
            next_profile = [[Fraction(0) for _ in range(self.states)] for _ in range(self.players)]
            next_best = [[Fraction(0) for _ in range(self.states)] for _ in range(self.players)]
            for player in range(self.players):
                rewards, transition = self.induced(profile, player)
                for state in range(self.states):
                    next_profile[player][state] = rewards[state] + sum(
                        transition[state][target] * profile_total[player][target]
                        for target in range(self.states)
                    )
                    actions: list[Q] = []
                    for action in range(self.action_counts[player]):
                        total = Fraction(0)
                        other_ranges = [
                            range(self.action_counts[p]) if p != player else (action,)
                            for p in range(self.players)
                        ]
                        for joint in product(*other_ranges):
                            probability = Fraction(1)
                            for other, chosen in enumerate(joint):
                                if other != player:
                                    probability *= profile[state][other][chosen]
                            key = (state, joint)
                            continuation = sum(
                                self.transitions[key][target] * best_total[player][target]
                                for target in range(self.states)
                            )
                            total += probability * (self.payoffs[key][player] + continuation)
                        actions.append(total)
                    next_best[player][state] = max(actions)
            profile_total, best_total = next_profile, next_best
        return tuple(
            tuple(
                (best_total[player][state] - profile_total[player][state]) / horizon
                for player in range(self.players)
            )
            for state in range(self.states)
        )
