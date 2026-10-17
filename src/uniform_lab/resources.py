"""Read-only access to versioned schemas and bundled examples."""

from __future__ import annotations

import json
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any


def _directory(name: str) -> Traversable:
    packaged = resources.files("uniform_lab").joinpath(name)
    if packaged.is_dir():
        return packaged
    source_tree = Path(__file__).resolve().parents[2] / name
    if source_tree.is_dir():
        return source_tree
    raise FileNotFoundError(f"bundled {name} directory is unavailable")


def _names(directory: str, suffix: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            entry.name for entry in _directory(directory).iterdir() if entry.name.endswith(suffix)
        )
    )


def schema_names() -> tuple[str, ...]:
    """Return the filenames of every bundled Draft 2020-12 schema."""

    return _names("schemas", ".schema.json")


def load_schema(name: str) -> dict[str, Any]:
    """Load one bundled schema by exact filename, without filesystem traversal."""

    if name not in schema_names():
        raise KeyError(f"unknown bundled schema {name!r}")
    value = json.loads(_directory("schemas").joinpath(name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"bundled schema {name!r} is not a JSON object")
    return value


def example_names() -> tuple[str, ...]:
    """Return top-level bundled JSON example filenames."""

    return _names("examples", ".json")


def load_example(name: str) -> dict[str, Any]:
    """Load one top-level bundled JSON example by exact filename."""

    if name not in example_names():
        raise KeyError(f"unknown bundled example {name!r}")
    value = json.loads(_directory("examples").joinpath(name).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"bundled example {name!r} is not a JSON object")
    return value
