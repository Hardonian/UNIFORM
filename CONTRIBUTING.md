# Contributing

Contributions are welcome, especially small exact counterexamples, independently checkable certificates, regression tests, schema improvements, and formalizations that narrow an explicitly stated trust boundary.

## Setup

```bash
uv sync --frozen --extra dev --extra solvers
uv run pytest -q
uv run ruff check .
uv run mypy
```

Rust changes must also pass rustfmt, Clippy with warnings denied, and release-mode tests. Lean changes must compile with `cd lean && lake build` and may not add `sorry` placeholders.

## Scientific claims

- State the strategy class, horizon/discount, grid, and solver timeout.
- Call a grid result “complete” only when every enumerated profile was evaluated.
- Do not promote a finite-grid observation to a continuous-domain theorem.
- Treat SAT models as candidates until exact re-evaluation passes.
- Treat UNSAT as scoped to the emitted formula unless a proof is independently checked.
- For resultants, distinguish necessary eliminant roots from back-substituted simultaneous solutions.
- Add a regression test and, for JSON, a versioned Draft 2020-12 schema.

## Pull requests

Keep unrelated changes separate. Update `CHANGELOG.md` for user-visible behavior and document compatibility effects. The pull request should summarize the exact verification commands run and any remaining trust assumptions.
