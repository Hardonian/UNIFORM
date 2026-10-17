"""Export verified quitting-game certificates as formal Lean 4 theorem files."""

from __future__ import annotations

import re

from .quitting import PeriodicRegretCertificate, QuittingGame
from .rational import rational_text

_LEAN_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_']*$")


def _checked_namespace(module_name: str) -> str:
    parts = module_name.split(".")
    if not parts or any(not _LEAN_IDENTIFIER.fullmatch(part) for part in parts):
        raise ValueError("module_name must be a dot-separated Lean identifier")
    return parts[-1]


def export_lean_certificate(
    game: QuittingGame,
    certificate: PeriodicRegretCertificate,
    module_name: str = "Uniform.GeneratedInstance",
    game_name: str = "QuittingInstance",
) -> str:
    """Generate a Lean file checking the certificate's concrete rational arithmetic.

    The generated theorem recomputes every reported regret from the supplied value and
    best-deviation arrays and checks the common bound.  It does not derive those arrays
    from the game/profile semantics, so it is an arithmetic certificate rather than a
    formal proof of equilibrium.
    """

    namespace = _checked_namespace(module_name)
    safe_game_name = " ".join(game_name.splitlines())

    lines: list[str] = [
        "module",
        "",
        "import Mathlib.Data.Rat.Defs",
        "import Mathlib.Tactic",
        "import Uniform.Certificate",
        "",
        "/-!",
        f"Exact rational arithmetic certificate for {safe_game_name}",
        f"Players: {game.players}",
        f"Maximum regret: {rational_text(certificate.maximum_regret)}",
        "",
        "Scope: this file checks the reported regret arithmetic and bound. It does not",
        "derive phase values or deviation values from the game/profile semantics.",
        "-/",
        "",
        f"namespace {namespace}",
        "",
        "open Uniform",
        "",
        f"def numPlayers : Nat := {game.players}",
        (
            "def continuationPayoff : List ℚ := ["
            f"{', '.join(rational_text(x) for x in game.continuation)}]"
        ),
        "def absorbingPayoffs : List (List ℚ) := [",
        *[
            f"  [{', '.join(rational_text(x) for x in game.payoffs[mask])}],"
            for mask in sorted(game.payoffs)
        ],
        "]",
        f"def maximumRegret : ℚ := {rational_text(certificate.maximum_regret)}",
        "",
    ]

    # Add phase values
    for phase_idx, values in enumerate(certificate.values):
        val_str = ", ".join(rational_text(v) for v in values)
        lines.append(f"def phase{phase_idx}Values : List ℚ := [{val_str}]")
    for phase_idx, dev_values in enumerate(certificate.best_deviation_values):
        dev_str = ", ".join(rational_text(d) for d in dev_values)
        lines.append(f"def phase{phase_idx}BestDeviations : List ℚ := [{dev_str}]")
    for phase_idx, regrets in enumerate(certificate.regrets):
        reg_str = ", ".join(rational_text(r) for r in regrets)
        lines.append(f"def phase{phase_idx}Regrets : List ℚ := [{reg_str}]")

    lines.append("")
    for phase_idx in range(certificate.period):
        lines.append(f"theorem phase{phase_idx}_regrets_recomputed :")
        lines.append(
            f"    phase{phase_idx}Regrets = List.zipWith regret "
            f"phase{phase_idx}Values phase{phase_idx}BestDeviations := by"
        )
        lines.append("  native_decide")
        lines.append("")

    joined_regrets = " ++ ".join(
        f"phase{phase_idx}Regrets" for phase_idx in range(certificate.period)
    )
    lines.append(f"def allRegrets : List ℚ := {joined_regrets}")
    lines.append("")
    lines.append("theorem certificate_regret_bound :")
    lines.append("    ∀ regretValue ∈ allRegrets, regretValue ≤ maximumRegret := by")
    lines.append("  native_decide")
    lines.append("")
    lines.append("theorem maximum_regret_attained : maximumRegret ∈ allRegrets := by")
    lines.append("  native_decide")
    lines.append("")

    lines.append(f"end {namespace}")
    lines.append("")

    return "\n".join(lines)
