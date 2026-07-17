# Security Policy

## Supported Versions

Only the latest public alpha release is currently supported with security updates.

## Reporting a Vulnerability

Report security issues privately to the maintainers. Do not open a public issue for an undisclosed vulnerability.

## Response Expectations

- We will acknowledge receipt within 48 hours.
- We will follow up with next steps or mitigation guidance as soon as triage completes.

## Current Signing Model

The bundled demo path is designed for local inspection and testing. Production-style signing depends on operator-managed signer configuration, trust registries, and revocation data rather than the shipped demo defaults.

For implementation-level hardening notes, see [the technical hardening document](docs/security-hardening.md).
