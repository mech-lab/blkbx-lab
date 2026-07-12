# Migration and Compatibility Notes

## Canonical Public Surface

The release-facing contract is:

- package: `blkbx-lab`
- CLI: `blkbx-lab`
- Python namespace: `blkbx_lab`
- artifacts: `ink_manifest.v1.json`, `ink_receipt.v1.json`, `receipt_comparison.v1.json`

## Deprecated Shims

- `mech_lab` imports the canonical `blkbx_lab` surface and emits a deprecation warning.
- `mechlab` delegates to the canonical CLI and emits a deprecation warning.

These shims exist for migration only and should not appear in new release-facing examples.

## In-Repo Historical Surfaces

The following paths remain in the repo for research or migration context, not as first-class public releases:

- `hybrid_mechlab/`
- `internal/trace/legacy_blt/`
- `internal/ink/legacy_mair/`
- `legacy/hybrid-mechlab-python/`
- `legacy/python-rust/`

## Qwen Note

The current public validation note is tracked in [the Qwen3.5 validation report](research/qwen35-validation-report.md). That report should describe only the public BLKBX Lab surface that actually ships.
