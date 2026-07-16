# Qwen3.5 Validation Report

## Scope

This document records the current public `blkbx-lab` Qwen3.5 validation surface as of July 16, 2026.

Canonical public commands:

```bash
blkbx-lab demo qwen35-claims --output-dir artifacts/qwen35-claims
blkbx-lab verify artifacts/qwen35-claims/ink_receipt.v2.json
blkbx-lab tamper artifacts/qwen35-claims/ink_receipt.v2.json
blkbx-lab verify artifacts/qwen35-claims/ink_receipt.tampered.v2.json
```

## Executive Result

Status:

- the installed public Qwen3.5 teaching path succeeds through `blkbx-lab`
- the demo emits `ink_manifest.v2.json` and `ink_receipt.v2.json`
- tamper detection fails verification as expected
- the current public release surface does not promise a real-model replay workflow

## Current Public Validation

The shipped public path uses the installed `qwen35` adapter and the Qwen3.5 claims demo:

- package surface: `blkbx-lab`
- Python namespace: `blkbx_lab`
- demo name: `qwen35-claims`
- receipt signer: local demo signer backend by default, with config-backed file signing also supported
- gate outcome for the bundled low-risk teaching demo: `pass`

Artifacts written by the public demo:

- `action.json`
- `ink_manifest.v2.json`
- `ink_receipt.v2.json`
- `ink_receipt.tampered.v2.json` after `tamper`

## Public Verification Result

The public verification story that currently ships is:

- `blkbx-lab demo` writes a manifest and receipt
- `blkbx-lab verify` returns success for the generated receipt
- `blkbx-lab tamper` writes a modified receipt
- `blkbx-lab verify` returns failure for the tampered receipt

Representative public Python flow:

```python
import blkbx_lab as bl

result = bl.demo(output_dir="artifacts/qwen35-claims")
verified = bl.verify(result.receipt_path)
tampered = bl.tamper(result.receipt_path)

assert verified.verification["valid"] is True
assert bl.verify(tampered.receipt_path).verification["valid"] is False
```

## Current Limits

- The public contract does not document hook-coverage analysis.
- The public contract does not document replay packs or MAIR-backed public artifacts.
- The public contract does not document a real-model replay workflow through `family` and `model` flags.
- The public adapter registry currently ships with `qwen35`.

## Reproducibility Appendix

Exact recorded local runtime and artifact paths from the archived validation workspace:

- native runtime root: `/Volumes/2.5SSDDD128/blkbx-lab-qwen35-validation`
- archived transformers source checkout: `/Volumes/2.5SSDDD128/blkbx-lab-qwen35-validation/src/transformers-upstream`
- archived output directory: `/Volumes/2.5SSDDD128/blkbx-lab-qwen35-validation/artifacts/qwen35-claims`
- archived manifest path: `/Volumes/2.5SSDDD128/blkbx-lab-qwen35-validation/artifacts/qwen35-claims/ink_manifest.v2.json`
- archived receipt path: `/Volumes/2.5SSDDD128/blkbx-lab-qwen35-validation/artifacts/qwen35-claims/ink_receipt.v2.json`

Recorded environment variables:

- `TMPDIR=/Volumes/2.5SSDDD128/blkbx-lab-qwen35-validation/tmp`
- `HF_HOME=/Volumes/2.5SSDDD128/blkbx-lab-qwen35-validation/hf-home`
- `HUGGINGFACE_HUB_CACHE=/Volumes/2.5SSDDD128/blkbx-lab-qwen35-validation/hf-cache`
- `TRANSFORMERS_CACHE=/Volumes/2.5SSDDD128/blkbx-lab-qwen35-validation/transformers-cache`
- `PIP_CACHE_DIR=/Volumes/2.5SSDDD128/blkbx-lab-qwen35-validation/pip-cache`
