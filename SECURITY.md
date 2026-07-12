# Security Policy

## Supported Versions

Only the latest alpha release is currently supported with security updates.

## Reporting a Vulnerability

Please report security vulnerabilities privately to the maintainers. Do not open a public issue.

## Current Signing Model

BLKBX Lab currently uses a built-in demo signing key (`dev-signature`) for generated Ink Receipts. That key exists to make local verification and tamper detection easy to inspect during development. It is not a production trust model.

## Production Use

Do not use the built-in demo key for production workflows. A future release will add support for real signing-key management so teams can provide their own secure keys for receipt issuance.
