# Lean certificate layer

This project pins Lean and Mathlib `v4.35.0`. It contains small established algebraic
lemmas behind the finite certificate calculations and deliberately contains no solver
models, `sorry`, or theorem asserting the open equilibrium-existence problem.

```powershell
cd lean
lake update
lake build 2>&1 | Tee-Object -FilePath lake-build.log
```

`lake-build.log` is generated evidence and should be committed only after a real build.
The initial host audit did not find Lean or Lake, so source presence alone is not
reported as a successful formal verification.
