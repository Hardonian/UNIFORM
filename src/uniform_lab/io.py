from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .absorption import AbsorptionPath, ContinuousHazard, DiscreteJump
from .quitting import QuittingGame
from .rational import Q, parse_rational, vector
from .stochastic import StationaryProfile, StochasticGame


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(value: Any, path: str | Path | None = None) -> str:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path is not None:
        Path(path).write_text(text, encoding="utf-8", newline="\n")
    return text


def load_quitting_game(path: str | Path) -> QuittingGame:
    data = load_json(path)
    if not isinstance(data, Mapping):
        raise TypeError("game file must contain a JSON object")
    schema = data.get("schema")
    if schema not in (None, "uniform.quitting-game/v1"):
        raise ValueError(f"unsupported game schema {schema!r}")
    return QuittingGame.from_dict(data)


def load_absorption_path(game: QuittingGame, path: str | Path) -> AbsorptionPath:
    data = load_json(path)
    if not isinstance(data, Mapping) or data.get("schema") != "uniform.absorption-path/v1":
        raise ValueError("unsupported absorption-path schema")
    raw_pieces = data.get("pieces")
    if not isinstance(raw_pieces, list):
        raise TypeError("absorption path pieces must be an array")
    pieces: list[ContinuousHazard | DiscreteJump] = []
    for index, raw in enumerate(raw_pieces):
        if not isinstance(raw, Mapping):
            raise TypeError(f"pieces[{index}] must be an object")
        kind = raw.get("kind")
        if kind == "continuous":
            density_raw = raw.get("density")
            if not isinstance(density_raw, Mapping):
                raise TypeError(f"pieces[{index}].density must be an object")
            density = {
                int(mask): parse_rational(value, field=f"pieces[{index}].density[{mask}]")
                for mask, value in density_raw.items()
            }
            pieces.append(
                ContinuousHazard(
                    parse_rational(raw.get("start"), field=f"pieces[{index}].start"),
                    parse_rational(raw.get("end"), field=f"pieces[{index}].end"),
                    density,
                )
            )
        elif kind == "jump":
            pieces.append(
                DiscreteJump(
                    parse_rational(raw.get("at"), field=f"pieces[{index}].at"),
                    vector(
                        raw.get("quit_probabilities"),
                        length=game.players,
                        field=f"pieces[{index}].quit_probabilities",
                    ),
                )
            )
        else:
            raise ValueError(f"pieces[{index}]: unknown kind {kind!r}")
    return AbsorptionPath(game, pieces)


def _joint_key(text: object, players: int) -> tuple[int, tuple[int, ...]]:
    if not isinstance(text, str) or "|" not in text:
        raise ValueError("stochastic keys must use 'state|action,action' syntax")
    state_text, actions_text = text.split("|", 1)
    actions = tuple(int(value) for value in actions_text.split(","))
    if len(actions) != players:
        raise ValueError(f"joint action key {text!r} has the wrong dimension")
    return int(state_text), actions


def load_stochastic_game(path: str | Path) -> StochasticGame:
    data = load_json(path)
    if not isinstance(data, Mapping) or data.get("schema") != "uniform.stochastic-game/v1":
        raise ValueError("unsupported stochastic-game schema")
    states = data.get("states")
    action_counts = data.get("action_counts")
    if isinstance(states, bool) or not isinstance(states, int):
        raise TypeError("states must be an integer")
    if not isinstance(action_counts, list) or any(
        isinstance(value, bool) or not isinstance(value, int) for value in action_counts
    ):
        raise TypeError("action_counts must be an integer array")
    players = len(action_counts)
    payoffs_raw, transitions_raw = data.get("payoffs"), data.get("transitions")
    if not isinstance(payoffs_raw, Mapping) or not isinstance(transitions_raw, Mapping):
        raise TypeError("payoffs and transitions must be objects")
    payoffs = {
        _joint_key(key, players): vector(value, length=players, field=f"payoffs[{key}]")
        for key, value in payoffs_raw.items()
    }
    transitions = {
        _joint_key(key, players): vector(value, length=states, field=f"transitions[{key}]")
        for key, value in transitions_raw.items()
    }
    return StochasticGame(states, tuple(action_counts), payoffs, transitions)


def load_stationary_profile(game: StochasticGame, path: str | Path) -> StationaryProfile:
    data = load_json(path)
    raw = data.get("profile") if isinstance(data, Mapping) else data
    if not isinstance(raw, list) or len(raw) != game.states:
        raise ValueError("stationary profile has the wrong state dimension")
    rows: list[tuple[tuple[Q, ...], ...]] = []
    for state, state_profile in enumerate(raw):
        if not isinstance(state_profile, list) or len(state_profile) != game.players:
            raise ValueError(f"profile[{state}] must contain one distribution per player")
        rows.append(
            tuple(
                vector(
                    probabilities,
                    length=game.action_counts[player],
                    field=f"profile[{state}][{player}]",
                )
                for player, probabilities in enumerate(state_profile)
            )
        )
    result = tuple(rows)
    game.validate_profile(result)
    return result
