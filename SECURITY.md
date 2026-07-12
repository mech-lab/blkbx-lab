# Security Policy

## Supported Versions

Only the latest alpha release is currently supported with security updates.

## Reporting a Vulnerability

Please report security vulnerabilities privately to the maintainers. Do not open a public issue.

## Dev Signing vs Production Signing

BLKBX Lab currently uses a hardcoded "dev-signature" key (`ed25519:dev`) for demonstration purposes. **Do not use this key in production.**

In a future release, we will introduce support for real Ed25519 signing via `cryptography` or `pynacl`, allowing you to provide your own secure keys for signing Ink Receipts.
