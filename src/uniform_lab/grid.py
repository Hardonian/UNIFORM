"""Deterministic exhaustive grids for periodic independent profiles."""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from .quitting import Profile, QuittingGame, periodic_regret_certificate
from .rational import Q, rational_text


@dataclass(frozen=True)
class GridCandidate:
    profile: Profile
    maximum_regret: Q

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": [[rational_text(value) for value in phase] for phase in self.profile],
            "maximum_regret": rational_text(self.maximum_regret),
        }


@dataclass(frozen=True)
class GridSearchResult:
    denominator: int
    period: int
    players: int
    total_profiles: int
    shard_index: int
    shard_count: int
    shard_profiles: int
    evaluated_profiles: int
    complete_shard: bool
    elapsed_seconds: float
    candidates: tuple[GridCandidate, ...]

    @property
    def complete_global_grid(self) -> bool:
        return self.complete_shard and self.shard_count == 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "uniform.periodic-grid-search/v1",
            "scope": (
                "all independent periodic profiles on the stated rational grid; "
                "regret covers deterministic unilateral policies of the same period"
            ),
            "denominator": self.denominator,
            "period": self.period,
            "players": self.players,
            "total_profiles": self.total_profiles,
            "shard": {
                "index": self.shard_index,
                "count": self.shard_count,
                "profiles": self.shard_profiles,
            },
            "evaluated_profiles": self.evaluated_profiles,
            "complete_shard": self.complete_shard,
            "complete_global_grid": self.complete_global_grid,
            "elapsed_seconds": self.elapsed_seconds,
            "best": [candidate.to_dict() for candidate in self.candidates],
            "global_game_claim": False,
        }


def periodic_grid_search(
    game: QuittingGame,
    denominator: int,
    period: int,
    *,
    keep: int = 10,
    max_profiles: int | None = None,
    shard_index: int = 0,
    shard_count: int = 1,
) -> GridSearchResult:
    if denominator < 1:
        raise ValueError("denominator must be positive")
    if period < 1:
        raise ValueError("period must be positive")
    if keep < 1:
        raise ValueError("keep must be positive")
    if max_profiles is not None and max_profiles < 1:
        raise ValueError("max_profiles must be positive")
    if shard_count < 1 or not 0 <= shard_index < shard_count:
        raise ValueError("shard must satisfy 0 <= shard_index < shard_count")
    values = tuple(Fraction(numerator, denominator) for numerator in range(denominator + 1))
    coordinates = game.players * period
    total_profiles = len(values) ** coordinates
    shard_profiles = (
        0
        if shard_index >= total_profiles
        else (total_profiles - 1 - shard_index) // shard_count + 1
    )
    best: list[GridCandidate] = []
    evaluated = 0
    started = time.monotonic()
    for profile_index in range(shard_index, total_profiles, shard_count):
        if max_profiles is not None and evaluated >= max_profiles:
            break
        remaining = profile_index
        flat_values = [Fraction(0)] * coordinates
        for coordinate in range(coordinates - 1, -1, -1):
            remaining, digit = divmod(remaining, len(values))
            flat_values[coordinate] = values[digit]
        flat = tuple(flat_values)
        profile = tuple(
            tuple(flat[phase * game.players : (phase + 1) * game.players])
            for phase in range(period)
        )
        regret = periodic_regret_certificate(game, profile).maximum_regret
        best.append(GridCandidate(profile, regret))
        best.sort(key=lambda candidate: (candidate.maximum_regret, candidate.profile))
        del best[keep:]
        evaluated += 1
    return GridSearchResult(
        denominator,
        period,
        game.players,
        total_profiles,
        shard_index,
        shard_count,
        shard_profiles,
        evaluated,
        evaluated == shard_profiles,
        time.monotonic() - started,
        tuple(best),
    )


def write_grid_csv(result: GridSearchResult, path: str | Path) -> None:
    columns = [
        f"q_{phase}_{player}" for phase in range(result.period) for player in range(result.players)
    ]
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["rank", "maximum_regret", *columns])
        writer.writeheader()
        for rank, candidate in enumerate(result.candidates, 1):
            row = {
                "rank": str(rank),
                "maximum_regret": rational_text(candidate.maximum_regret),
            }
            for phase in range(result.period):
                for player in range(result.players):
                    row[f"q_{phase}_{player}"] = rational_text(candidate.profile[phase][player])
            writer.writerow(row)
