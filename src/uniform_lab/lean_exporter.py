"""Export verified quitting-game certificates as formal Lean 4 theorem files."""

from __future__ import annotations

from .quitting import PeriodicRegretCertificate, QuittingGame
from .rational import rational_text


def export_lean_certificate(
    game: QuittingGame,
    certificate: PeriodicRegretCertificate,
    module_name: str = "Uniform.GeneratedInstance",
    game_name: str = "QuittingInstance",
) -> str:
    """Generate a formal Lean 4 source file certifying the periodic regret of a game."""

    lines: list[str] = [
        "module",
        "",
        "import Mathlib.Data.Rat.Defs",
        "import Mathlib.Tactic",
        "import Uniform.Certificate",
        "",
        "/-!",
        f"Formal certificate for {game_name}",
        f"Players: {game.players}",
        f"Maximum regret: {rational_text(certificate.maximum_regret)}",
        "-/",
        "",
        f"namespace {module_name.split('.')[-1]}",
        "",
        "open Uniform",
        "",
        f"def numPlayers : Nat := {game.players}",
        (
            "def continuationPayoff : List ℚ := ["
            f"{', '.join(rational_text(x) for x in game.continuation)}]"
        ),
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
    # Add regret bound theorem
    lines.append("theorem certificate_regret_bound :")
    lines.append(f"    maximumRegret ≤ ({rational_text(certificate.maximum_regret)} : ℚ) := by")
    lines.append("  unfold maximumRegret")
    lines.append("  decide")
    lines.append("")

    lines.append(f"end {module_name.split('.')[-1]}")
    lines.append("")

    return "\n".join(lines)
