from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Any

from .quitting import QuittingGame


def candidate_to_game(candidate: Mapping[str, Any]) -> QuittingGame:
    raw_payoffs = candidate.get("payoffs")
    if not isinstance(raw_payoffs, Sequence) or len(raw_payoffs) != 15:
        raise ValueError("a four-player screen candidate must contain 15 payoff rows")
    payoffs: dict[int, tuple[Fraction, ...]] = {}
    for mask, raw_row in enumerate(raw_payoffs, start=1):
        if not isinstance(raw_row, Sequence) or len(raw_row) != 4:
            raise ValueError(f"candidate payoff row {mask} must have four entries")
        if any(isinstance(value, bool) or not isinstance(value, int) for value in raw_row):
            raise TypeError("Rust screening handoff accepts integer payoffs only")
        payoffs[mask] = tuple(Fraction(value) for value in raw_row)
    continuation_raw = candidate.get("continuation", [0, 0, 0, 0])
    if not isinstance(continuation_raw, Sequence) or len(continuation_raw) != 4:
        raise ValueError("candidate continuation must have four entries")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in continuation_raw):
        raise TypeError("Rust screening handoff accepts integer continuation payoffs only")
    return QuittingGame(
        players=4,
        payoffs=payoffs,
        continuation=tuple(Fraction(value) for value in continuation_raw),
        title=f"Rust screen candidate {candidate.get('sample_id', 'unknown')}",
        provenance={
            "kind": "generated-screen-candidate",
            "seed": candidate.get("seed"),
            "sample_id": candidate.get("sample_id"),
        },
    )


def verify_screen_document(document: Mapping[str, Any]) -> tuple[QuittingGame, ...]:
    if document.get("schema") != "uniform.rust-screen/v1":
        raise ValueError("unsupported Rust screen schema")
    candidates = document.get("candidates")
    if not isinstance(candidates, list):
        raise TypeError("screen candidates must be an array")
    games = tuple(candidate_to_game(candidate) for candidate in candidates)
    for game in games:
        if game.pure_instant_equilibria():
            raise ValueError("Rust/Python disagreement: candidate has a pure instant equilibrium")
    return games
