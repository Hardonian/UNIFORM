# Release checklist

1. Choose a PEP 440 version and update `pyproject.toml`, `uniform_lab.__version__`, `CITATION.cff`, and `CHANGELOG.md`.
2. Run `uv lock --check` and the Python/Rust/Lean commands in the README.
3. Run `uv run python scripts/reproduce_all.py` and inspect the scoped audit certificate.
4. Build with `uv build`; run `uvx twine check dist/*`; install the wheel into an empty virtual environment and exercise the CLI and bundled resources.
5. Review every changed schema identifier and compatibility implication.
6. Confirm documentation describes finite grids, solver results, eliminants, generated Lean arithmetic, and checked-in Lean theorems at their actual scope.
7. Review dependency and container changes, then create a signed tag matching `v<package-version>`.
8. Let the protected `pypi` GitHub environment approve trusted publishing. Verify the installed artifact and attach the audit certificate to release notes.

Do not publish `1.0.0` while any release gate is failing or while a known correctness issue is described only as a documentation caveat.
