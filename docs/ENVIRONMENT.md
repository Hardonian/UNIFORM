# Reproducibility environment — 2026-10-16

- Base commit: `48f4421c3f8632966922f202cc861a12911b7b3f`
- Working branch: `feat/full-research-lab`
- Host OS: Windows, PowerShell
- CPU: AMD Ryzen AI 9 HX 370 with Radeon 890M, 12 cores / 24 logical processors
- RAM reported by WMI: 33,949,601,792 bytes
- GPU reported by WMI: AMD Radeon 890M Graphics; no NVIDIA device or `nvidia-smi`
- Python: 3.12.10 system; uv-managed project interpreter selected by `uv`
- uv: available at `C:\Users\scott\.local\bin\uv.exe`
- Rust: rustc 1.98.1, cargo 1.98.1
- Elan 4.2.4 and Lean/Lake 4.35.0: installed during the run; pinned Mathlib build
  completed successfully (`lean/lake-build.log`, 3,139 jobs)
- Z3 command-line executable: absent; optional Python binding 5.3.1 installed and tested
- cvc5 command-line executable: absent; optional Python binding 1.4.2 installed and tested

Follow-up package verification built `uniform-lab` 0.2.0 as both wheel and sdist. The
wheel contains the algebraic, solver-campaign, exact-grid, and rational-polytope modules
plus nine JSON schemas. The expanded suite passes 31 tests; Ruff and strict Mypy pass.
Z3 and cvc5 again produced SAT models in the smoke campaign and both were independently
checked. Native UNSAT proof retention was exercised for both bindings on an inconsistent
linear-real fixture. The pinned Lean build was rerun explicitly through
`C:\Users\scott\.elan\bin\lake.exe` and completed 3,139 jobs.

The checked-in Rust observation scanned 1,000,000 generated games with seed 7. Its
JSON records elapsed time and throughput. This laptop is not the EPYC/NVIDIA host
described by the supplied directive, so no EPYC, CUDA, or NVIDIA execution is claimed.
