# Migration and Compatibility Notes

## Canonical Shipped Surface

The release-facing contract is:

- install package: `mechlab-sdk`
- primary CLI: `blkbx-lab`
- primary Python namespace: `blkbx_lab`
- public artifacts: `ink_manifest.v2.json`, `ink_receipt.v2.json`, `receipt_comparison.v2.json`

## Compatibility Aliases

The wheel still carries compatibility aliases for older documentation and automation:

- CLI alias: `mechlab`
- Python alias: `mech_lab`

Treat them as migration surfaces, not the primary onboarding path.

## Adapter Compatibility

The shipped deterministic demo accepts these selectors and normalizes them to `qwen35`:

- `qwen35`
- `qwen35-claims`
- `qwen3.5`
- `Qwen/Qwen3.5-2B`

Unsupported `adapter`, `family`, `model`, `backend`, or `profile` inputs fail loudly outside that compatibility set.

## Host and Kernel Boundary

The current public artifacts remain `v2` JSON surfaces verified through the host layer:

- `ink-host` issues and verifies current receipt artifacts
- `ink-core` is the domain-neutral trust waist underneath that host surface
- `ink-verify` provides verification primitives without redefining the public JSON contract

## Repo Scope

- `products/*` are in-repo source slices
- `web/rails` and `packages/ink-ts-verify` are in-repo scaffolds
- historical planning and exploratory notes live in [`docs/archive/`](archive/README.md)
