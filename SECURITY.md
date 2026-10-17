# Security policy

## Supported versions

Security fixes are applied to the latest published release. Pre-release builds are supported on a best-effort basis until `1.0.0`.

## Reporting

Please report suspected vulnerabilities privately through GitHub Security Advisories for `Hardonian/UNIFORM`. Do not include sensitive data in a public issue. Include the affected version, reproduction steps, impact, and any proposed mitigation.

## Deployment boundary

`uniform serve` is a local research workbench, not a multi-tenant production service. It has no authentication or TLS termination. It defaults to `127.0.0.1`, limits JSON bodies to 1 MiB, bounds web-triggered grid work, and does not enable cross-origin access. If deliberately bound to a non-loopback interface, place it behind authentication, TLS, and network controls.

Solver inputs, JSON documents, and generated Lean files should be treated as untrusted data. Run expensive external solvers with resource limits and never interpret a retained native proof as independently checked unless a compatible semantic proof checker has accepted it.
