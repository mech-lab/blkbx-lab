# Migration and Compatibility Notes

## Canonical Public Surface

The release-facing contract is:

- package: `blkbx-lab`
- CLI: `blkbx-lab`
- Python namespace: `blkbx_lab`
- artifacts: `ink_manifest.v2.json`, `ink_receipt.v2.json`, `receipt_comparison.v2.json`

## Deprecated Selectors

The public package still tolerates some deprecated adapter-selection inputs for the installed deterministic demo:

- `qwen35`
- `qwen35-claims`
- `qwen3.5`
- `Qwen/Qwen3.5-2B`

Deprecated `backend`, `family`, `model`, and `profile` knobs are normalized or rejected fail-loudly; they are not separate product surfaces.

## Repo Scope

The product repo no longer ships research trees, legacy compatibility namespaces, notebooks, or experimental Rust crates. Those belong in a separate research repo if they still need history preserved.

## Signing Compatibility

- current default encoding: `INK-CORE-TLV-V2`
- explicit compatibility encoding: `INK-CORE-TRANSCRIPT-V1`
- governed alternate encoding: `INK-CORE-JSON-CANONICAL-V1`

The `signing.transcript_encoding` field is part of the public compatibility contract. Verifiers must treat it as authoritative rather than assuming a single implicit transcript format.

## Qwen Note

The current public validation note is tracked in [the Qwen3.5 validation report](research/qwen35-validation-report.md). That report should describe only the public BLKBX Lab surface that actually ships.
