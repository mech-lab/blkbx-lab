# BLKBX Lab

> Open-source Ink Receipt gates for accountable AI agents.
>
> Qwen3.5 is the installed demo. Receipt gates are the standard.

BLKBX Lab lets developers wrap AI agents with signed, verifiable action gates. It ships with a Qwen3.5 claims demo, but its thin model-adapter waist works with any open Gated DeltaNet-style or hybrid recurrent-attention model.

## Install

```bash
pip install --pre blkbx-lab
```

## 60-second quickstart

CLI:

```bash
blkbx-lab demo qwen35-claims --output-dir artifacts/qwen35-claims
blkbx-lab verify artifacts/qwen35-claims/ink_receipt.v1.json
blkbx-lab tamper artifacts/qwen35-claims/ink_receipt.v1.json
blkbx-lab verify artifacts/qwen35-claims/ink_receipt.tampered.json
```

Python:

```python
import blkbx_lab as bl

bundle = bl.demo("qwen35-claims", output_dir="artifacts/qwen35-claims")
print(bundle.receipt_path)
print(bl.report(bundle))
```

## What You Get

- Action Evidence Bundle: `ink_manifest.v1.json` plus the required run artifacts.
- Receipt: `ink_receipt.v1.json` for gate decisions.
- Comparison Packet: `receipt_comparison.v1.json` for run-to-run diffs.

## How It Works

```text
blkbx-lab CLI / blkbx_lab SDK
        |
        +-- internal/trace   model event capture, action proposal capture
        |
        +-- internal/ink     manifest, canonicalization, signing, verification
        |
        +-- internal/gates   gate policies, decisions, receipt issuance
        |
        +-- adapters/        qwen35, vllm, sglang, openai-compatible
```

## Docs And Status

- [CLI and API contract](docs/mvp-cli-api-contract.md)
- [Public object spec](docs/public-object-spec.md)
- [Developer architecture](docs/developer-architecture.md)

Release status:

- Alpha release surface: product repo `blkbx-lab`, published package `blkbx-lab`
- Public CLI: `blkbx-lab`
- Public Python namespace: `blkbx_lab`
