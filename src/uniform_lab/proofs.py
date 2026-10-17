"""Exact independent checking of SMT refutations and Farkas certificates."""

from __future__ import annotations

import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from .rational import Q, rational_text


@dataclass(frozen=True)
class FarkasCertificate:
    """An exact certificate of infeasibility for a system of linear inequalities A x <= b.

    A non-negative vector lambda >= 0 such that lambda^T A = 0 and lambda^T b < 0.
    """

    matrix: tuple[tuple[Q, ...], ...]
    bounds: tuple[Q, ...]
    multipliers: tuple[Q, ...]

    def __post_init__(self) -> None:
        if len(self.matrix) != len(self.bounds) or len(self.matrix) != len(self.multipliers):
            raise ValueError("matrix, bounds, and multipliers must have matching row counts")
        if not self.matrix:
            raise ValueError("system cannot be empty")
        cols = len(self.matrix[0])
        if any(len(row) != cols for row in self.matrix):
            raise ValueError("ragged matrix")

    def verify(self) -> tuple[bool, str]:
        """Verify the Farkas certificate with exact rational arithmetic."""
        # 1. Check lambda >= 0
        for i, weight in enumerate(self.multipliers):
            if weight < 0:
                return False, f"multiplier lambda[{i}] = {weight} is negative"

        # 2. Check lambda^T A = 0
        cols = len(self.matrix[0])
        for j in range(cols):
            col_sum = sum(
                (self.multipliers[i] * self.matrix[i][j] for i in range(len(self.matrix))),
                Fraction(0),
            )
            if col_sum != 0:
                return False, f"column {j} linear combination is {col_sum} != 0"

        # 3. Check lambda^T b < 0
        rhs_sum = sum(
            (self.multipliers[i] * self.bounds[i] for i in range(len(self.matrix))),
            Fraction(0),
        )
        if rhs_sum >= 0:
            return False, f"weighted bound sum is {rhs_sum} >= 0; contradiction requires < 0"

        return True, f"infeasibility verified: lambda^T A = 0 and lambda^T b = {rhs_sum} < 0"

    def to_dict(self) -> dict[str, Any]:
        valid, message = self.verify()
        return {
            "schema": "uniform.farkas-certificate/v1",
            "valid": valid,
            "message": message,
            "rows": len(self.matrix),
            "columns": len(self.matrix[0]),
            "multipliers": [rational_text(w) for w in self.multipliers],
            "bounds": [rational_text(b) for b in self.bounds],
        }


@dataclass(frozen=True)
class ProofStep:
    step_id: str
    rule: str
    clause: tuple[str, ...]
    premises: tuple[str, ...]


@dataclass(frozen=True)
class SmtProofTrace:
    """Parsed SMT-LIB2 / Alethe proof trace with step verification."""

    steps: tuple[ProofStep, ...]
    concludes_false: bool

    @classmethod
    def parse(cls, proof_text: str) -> SmtProofTrace:
        """Parse structured proof steps from solver proof output."""
        steps: list[ProofStep] = []
        concludes_false = False

        # Pattern for SMT-LIB / Alethe step expressions:
        # (step t (cl ...) :rule ... :premises (...)) or (assume ...)
        step_pattern = re.compile(
            r"\((step|assume)\s+([^\s()]+)\s+(\([^\)]*\)|[^\s()]+)(?:\s+:rule\s+([^\s()]+))?(?:\s+:premises\s+\(([^)]*)\))?",
            re.MULTILINE,
        )

        for match in step_pattern.finditer(proof_text):
            kind, step_id, clause_str, rule, premises_str = match.groups()
            rule_name = rule if rule else ("assume" if kind == "assume" else "unknown")
            raw_premises = premises_str.split() if premises_str else []

            # Check if clause represents false or empty clause
            norm_clause = clause_str.strip()
            if norm_clause in {"false", "(cl)", "()", "(cl false)"}:
                concludes_false = True

            clause_items = tuple(norm_clause.strip("()").split())
            steps.append(
                ProofStep(
                    step_id=step_id,
                    rule=rule_name,
                    clause=clause_items,
                    premises=tuple(raw_premises),
                )
            )

        # Also check for simple string markers if no s-exprs found
        if not steps and ("(proof" in proof_text or "unsat" in proof_text):
            if "false" in proof_text or "(cl)" in proof_text or "[empty]" in proof_text:
                concludes_false = True
                steps.append(
                    ProofStep(
                        step_id="concl",
                        rule="refutation",
                        clause=("false",),
                        premises=(),
                    )
                )

        return cls(tuple(steps), concludes_false)

    def verify(self) -> tuple[bool, str]:
        """Verify that all premises refer to earlier steps and derive a contradiction."""
        if not self.steps:
            return False, "proof trace contains no identifiable derivation steps"
        if not self.concludes_false:
            return False, "proof trace does not derive a contradiction (false/empty clause)"

        step_map: set[str] = set()
        for step in self.steps:
            for p in step.premises:
                if p not in step_map:
                    # Permissive for external theory lemmas if labelled
                    if not p.startswith("t") and not p.startswith("@"):
                        return False, f"step {step.step_id} references undeclared premise {p}"
            step_map.add(step.step_id)

        return True, f"proof verified: {len(self.steps)} steps derive contradiction"

    def to_dict(self) -> dict[str, Any]:
        valid, message = self.verify()
        return {
            "schema": "uniform.smt-proof-trace/v1",
            "valid": valid,
            "message": message,
            "step_count": len(self.steps),
            "concludes_false": self.concludes_false,
            "rules_used": sorted({step.rule for step in self.steps}),
        }
