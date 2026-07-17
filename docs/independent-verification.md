# Independent Verification

BLKBX Lab’s current verification story is local, inspectable, and native.

## Current Verification Surfaces

- `blkbx-lab verify` for the primary Python-hosted public flow
- `ink` for kernel-facing native verification commands
- `ink-tui` for a zero-JS terminal verification workflow

## Current Policy Surfaces

The current public verification path operates over:

- `ink_receipt.v2.json`
- optional `ink_manifest.v2.json`
- optional controls payloads
- optional trust registry, revocation list, and verification policy files

## Trust Boundary

- The shipped trust root is native Rust verification, not browser JavaScript.
- `web/rails` and `web/verify` are scaffolds and do not redefine the verification boundary.
- Verification is designed to work without network access during the check itself.

## Strict and Compatibility Verification

- New docs and examples should target the current `v2` artifact set.
- Compatibility aliases and selector normalization are part of the migration surface, not the primary verification story.
