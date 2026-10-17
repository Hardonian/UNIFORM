# Reference verification environment — 2026-10-16

The release candidate was hardened on Windows with Python 3.12.10, uv 0.9.5, rustc/cargo 1.98.1, Lean 4.35.0/Lake 5.0.0, Z3 Python bindings, and cvc5 Python bindings. CI independently targets Python 3.11, 3.12, and 3.13 on Ubuntu and exercises both solver bindings.

These versions describe one verification environment, not a hardware or timing requirement. Exact rational outputs and hashes are the reproducible objects. Paths, timestamps, solver timing, Rust throughput, and Lake build-job counts vary by environment.

Run `uniform environment` for machine-readable discovery metadata, `uniform doctor` for component availability, and `python scripts/reproduce_all.py` for the actual release gates. A prior run log is not evidence that the current checkout builds.

The checked-in Rust benchmark records its own seed, sample count, elapsed time, and throughput. Do not transfer that throughput figure to other hosts without rerunning the same command and recording the new environment.
