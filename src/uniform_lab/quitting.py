"""Exact arithmetic for finite-player quitting games.

Bit ``i`` of an outcome mask is one exactly when player ``i`` quits.  Mask zero is
the nonabsorbing all-continue action and uses ``continuation`` only if play never
absorbs (or at a finite-certificate boundary).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import product
from typing import Any

from .rational import Q, parse_rational, rational_text, vector


def _mask_from_key(key: object, players: int) -> int:
    if isinstance(key, int):
        mask = key
    elif isinstance(key, str):
        text = key.strip()
        if text.startswith("0b"):
            mask = int(text, 2)
        elif len(text) == players and set(text) <= {"0", "1"}:
            # Human-facing bit strings are player order: player 0 is the leftmost bit.
            mask = sum((ch == "1") << i for i, ch in enumerate(text))
        else:
            mask = int(text)
    else:
        raise TypeError(f"payoff mask must be an integer or string, got {type(key).__name__}")
    if not 1 <= mask < (1 << players):
        raise ValueError(f"absorbing mask {mask} is outside 1..{(1 << players) - 1}")
    return mask


@dataclass(frozen=True)
class QuittingGame:
    players: int
    payoffs: Mapping[int, tuple[Q, ...]]
    continuation: tuple[Q, ...]
    title: str = ""
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.players < 1:
            raise ValueError("players must be positive")
        expected = set(range(1, 1 << self.players))
        actual = set(self.payoffs)
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise ValueError(
                f"payoffs must cover every absorbing mask; missing={missing}, extra={extra}"
            )
        if len(self.continuation) != self.players:
            raise ValueError("continuation payoff has the wrong dimension")
        for mask, payoff in self.payoffs.items():
            if len(payoff) != self.players:
                raise ValueError(f"mask {mask} payoff has the wrong dimension")
            if not all(isinstance(value, Fraction) for value in payoff):
                raise TypeError(f"mask {mask} contains a non-Fraction payoff")
        if not all(isinstance(value, Fraction) for value in self.continuation):
            raise TypeError("continuation contains a non-Fraction payoff")

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> QuittingGame:
        players_raw = data.get("players")
        if isinstance(players_raw, bool) or not isinstance(players_raw, int):
            raise TypeError("players must be an integer")
        players = players_raw
        raw_payoffs = data.get("payoffs")
        if not isinstance(raw_payoffs, Mapping):
            raise TypeError("payoffs must be an object keyed by absorbing masks")
        payoffs: dict[int, tuple[Q, ...]] = {}
        for raw_mask, raw_vector in raw_payoffs.items():
            mask = _mask_from_key(raw_mask, players)
            if mask in payoffs:
                raise ValueError(f"duplicate normalized payoff mask {mask}")
            payoffs[mask] = vector(raw_vector, length=players, field=f"payoffs[{raw_mask!r}]")
        continuation = vector(data.get("continuation"), length=players, field="continuation")
        provenance = data.get("provenance", {})
        if not isinstance(provenance, Mapping):
            raise TypeError("provenance must be an object")
        return cls(
            players=players,
            payoffs=payoffs,
            continuation=continuation,
            title=str(data.get("title", "")),
            provenance=dict(provenance),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "uniform.quitting-game/v1",
            "title": self.title,
            "players": self.players,
            "continuation": [rational_text(value) for value in self.continuation],
            "payoffs": {
                str(mask): [rational_text(value) for value in self.payoffs[mask]]
                for mask in sorted(self.payoffs)
            },
            "provenance": dict(self.provenance),
        }

    def payoff(self, mask: int) -> tuple[Q, ...]:
        return self.continuation if mask == 0 else self.payoffs[mask]

    def pure_instant_equilibria(self) -> tuple[int, ...]:
        """Pure Nash outcomes of the one-shot continuation-payoff game."""

        equilibria: list[int] = []
        for mask in range(1 << self.players):
            base = self.payoff(mask)
            if all(
                self.payoff(mask ^ (1 << player))[player] <= base[player]
                for player in range(self.players)
            ):
                equilibria.append(mask)
        return tuple(equilibria)


Profile = tuple[tuple[Q, ...], ...]


def normalize_profile(game: QuittingGame, raw: Sequence[Sequence[object]]) -> Profile:
    if not raw:
        raise ValueError("a periodic profile needs at least one phase")
    phases: list[tuple[Q, ...]] = []
    for t, phase in enumerate(raw):
        if len(phase) != game.players:
            raise ValueError(f"phase {t}: expected {game.players} probabilities")
        parsed = tuple(
            parse_rational(value, field=f"profile[{t}][{i}]") for i, value in enumerate(phase)
        )
        if any(value < 0 or value > 1 for value in parsed):
            raise ValueError(f"phase {t}: probabilities must lie in [0,1]")
        phases.append(parsed)
    return tuple(phases)


def outcome_probability(phase: Sequence[Q], mask: int) -> Q:
    probability = Fraction(1)
    for player, quit_probability in enumerate(phase):
        probability *= quit_probability if mask & (1 << player) else 1 - quit_probability
    return probability


def stage_terms(game: QuittingGame, phase: Sequence[Q]) -> tuple[Q, tuple[Q, ...]]:
    survival = outcome_probability(phase, 0)
    rewards = [Fraction(0) for _ in range(game.players)]
    for mask in range(1, 1 << game.players):
        probability = outcome_probability(phase, mask)
        for player in range(game.players):
            rewards[player] += probability * game.payoffs[mask][player]
    return survival, tuple(rewards)


def _cycle_values_from_terms(
    survival: Sequence[Q], rewards: Sequence[Sequence[Q]], terminal: Sequence[Q]
) -> tuple[tuple[Q, ...], ...]:
    period = len(survival)
    players = len(terminal)
    cycle_survival = Fraction(1)
    for value in survival:
        cycle_survival *= value
    if cycle_survival == 1:
        return tuple(tuple(terminal) for _ in range(period))

    result: list[tuple[Q, ...]] = []
    for start in range(period):
        prefix = Fraction(1)
        numerator = [Fraction(0) for _ in range(players)]
        for offset in range(period):
            phase = (start + offset) % period
            for player in range(players):
                numerator[player] += prefix * rewards[phase][player]
            prefix *= survival[phase]
        result.append(tuple(value / (1 - cycle_survival) for value in numerator))
    return tuple(result)


def periodic_values(game: QuittingGame, profile: Profile) -> tuple[tuple[Q, ...], ...]:
    """Conditional limiting payoff at the beginning of every phase."""

    terms = tuple(stage_terms(game, phase) for phase in profile)
    return _cycle_values_from_terms(
        tuple(term[0] for term in terms), tuple(term[1] for term in terms), game.continuation
    )


def replace_player(profile: Profile, player: int, policy: Sequence[int]) -> Profile:
    phases: list[tuple[Q, ...]] = []
    for phase, action in zip(profile, policy, strict=True):
        changed = list(phase)
        changed[player] = Fraction(action)
        phases.append(tuple(changed))
    return tuple(phases)


@dataclass(frozen=True)
class PeriodicRegretCertificate:
    scope: str
    period: int
    values: tuple[tuple[Q, ...], ...]
    best_deviation_values: tuple[tuple[Q, ...], ...]
    regrets: tuple[tuple[Q, ...], ...]
    maximizing_policies: tuple[tuple[tuple[tuple[int, ...], ...], ...], ...]

    @property
    def maximum_regret(self) -> Q:
        return max(value for phase in self.regrets for value in phase)

    def to_dict(self) -> dict[str, Any]:
        def matrix(values: Iterable[Iterable[Q]]) -> list[list[str]]:
            return [[rational_text(value) for value in row] for row in values]

        return {
            "schema": "uniform.periodic-regret-certificate/v1",
            "scope": self.scope,
            "period": self.period,
            "values_by_start_phase": matrix(self.values),
            "best_deviation_values_by_start_phase": matrix(self.best_deviation_values),
            "regrets_by_start_phase": matrix(self.regrets),
            "maximum_regret": rational_text(self.maximum_regret),
            "maximizing_policies": [
                [list(policy) for policy in per_player] for per_player in self.maximizing_policies
            ],
        }


def periodic_regret_certificate(game: QuittingGame, profile: Profile) -> PeriodicRegretCertificate:
    """Check all pure periodic deviations of the same period, from every phase.

    Against independent periodic opponents, randomizing between actions cannot improve
    on a pure policy.  The certificate is deliberately labelled as a periodic-policy
    certificate; it is not a claim about arbitrary history-dependent deviations.
    """

    values = periodic_values(game, profile)
    period = len(profile)
    best = [[values[t][i] for i in range(game.players)] for t in range(period)]
    argmax: list[list[list[tuple[int, ...]]]] = [
        [[] for _ in range(game.players)] for _ in range(period)
    ]
    for player in range(game.players):
        for policy in product((0, 1), repeat=period):
            deviation_values = periodic_values(game, replace_player(profile, player, policy))
            for start in range(period):
                candidate = deviation_values[start][player]
                if candidate > best[start][player]:
                    best[start][player] = candidate
                    argmax[start][player] = [policy]
                elif candidate == best[start][player]:
                    argmax[start][player].append(policy)
    best_tuple = tuple(tuple(row) for row in best)
    regrets = tuple(
        tuple(best_tuple[t][i] - values[t][i] for i in range(game.players)) for t in range(period)
    )
    policies = tuple(tuple(tuple(items) for items in phase) for phase in argmax)
    return PeriodicRegretCertificate(
        scope=(
            "all deterministic periodic unilateral deviations of the stated period, "
            "every start phase"
        ),
        period=period,
        values=values,
        best_deviation_values=best_tuple,
        regrets=regrets,
        maximizing_policies=policies,
    )


@dataclass(frozen=True)
class HorizonCertificate:
    horizon: int
    start_phase: int
    value: tuple[Q, ...]
    best_deviation_value: tuple[Q, ...]
    regret: tuple[Q, ...]

    @property
    def maximum_regret(self) -> Q:
        return max(self.regret)


def finite_horizon_certificate(
    game: QuittingGame, profile: Profile, horizon: int, *, start_phase: int = 0
) -> HorizonCertificate:
    """Exact truncated-terminal certificate with ``continuation`` at the boundary."""

    if horizon < 0:
        raise ValueError("horizon must be non-negative")
    period = len(profile)
    continuation = list(game.continuation)
    best = list(game.continuation)
    for remaining in range(1, horizon + 1):
        phase_index = (start_phase + horizon - remaining) % period
        phase = profile[phase_index]
        survival, rewards = stage_terms(game, phase)
        continuation = [rewards[i] + survival * continuation[i] for i in range(game.players)]
        prior_best = list(best)
        for player in range(game.players):
            action_values: list[Q] = []
            for action in (0, 1):
                changed = list(phase)
                changed[player] = Fraction(action)
                dev_survival, dev_rewards = stage_terms(game, changed)
                action_values.append(dev_rewards[player] + dev_survival * prior_best[player])
            best[player] = max(action_values)
    value = tuple(continuation)
    best_value = tuple(best)
    regret = tuple(best_value[i] - value[i] for i in range(game.players))
    return HorizonCertificate(horizon, start_phase, value, best_value, regret)
