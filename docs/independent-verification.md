# Independent Verification

BLKBX Lab’s current verification story is local, inspectable, and native.

## Current Verification Surfaces

- `blkbx-lab verify` for the primary Python-hosted public flow
- `ink` for kernel-facing native verification commands
- `ink-tui` for a zero-JS terminal verification workflow
- `web/verify` for the browser-facing WASM wrapper over the shared Rust verifier

## Current Policy Surfaces

The current public verification path operates over:

- `ink_receipt.v2.json`
- optional `ink_manifest.v2.json`
- optional controls payloads
- optional trust registry, revocation list, and verification policy files

## Trust Boundary

- The shipped trust root is native Rust verification, not browser JavaScript.
- `web/verify` delegates verification to `ink-wasm`; it does not carry a second verification implementation in JavaScript.
- `web/rails` can serve or link to the browser verifier and emit handoff URLs, but it does not redefine the verification boundary.
- Verification is designed to work without network access during the check itself.

## Strict and Compatibility Verification

- New docs and examples should target the current `v2` artifact set.
- Compatibility aliases and selector normalization are part of the migration surface, not the primary verification story.

## Lloyd's Labs Demo

The MAND8 Lloyd's Labs runbook is documented in [mand8-lloyds-labs-demo.md](mand8-lloyds-labs-demo.md).

For the fixed Friday, July 17, 2026 demo data:

- seeded MAND8 workspaces do not expose Rails artifact handoff URLs unless they truly carry a portable `ink.receipt.v2` companion
- the browser verifier still accepts real Rails artifact handoff URLs at `/verify/index.html?artifact_url=...`
- the page renders pass, warning, or fail from the Rust `ink.verification-report.v1` output
- the native parity command is `ink receipt --receipt ... --manifest ... --trust-registry ... --policy ...`
