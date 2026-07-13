# BLKBX Lab

Open-source Ink Receipt gates for accountable AI agents.

`BLKBX Lab` wraps agent actions with local policy gates and emits signed artifacts that another engineer can verify offline. The current public surface is intentionally small: it ships a Qwen3.5 claims demo, writes Ink manifests and receipts, and keeps the release contract centered on `blkbx-lab` / `blkbx_lab`.

## Install

```bash
pip install --pre blkbx-lab
```

## Quickstart

```bash
blkbx-lab demo qwen35-claims --output-dir artifacts/blkbx-lab-demo
blkbx-lab verify artifacts/blkbx-lab-demo/ink_receipt.v1.json
blkbx-lab tamper artifacts/blkbx-lab-demo/ink_receipt.v1.json
blkbx-lab verify artifacts/blkbx-lab-demo/ink_receipt.tampered.json
```

```python
import blkbx_lab as bl

result = bl.demo(output_dir="artifacts/blkbx-lab-demo")
print(result.manifest_path)
print(result.receipt_path)
print(bl.verify(result.receipt_path).report)
```

## What You Get

- Action Evidence Bundle: `ink_manifest.v1.json`
- Receipt: `ink_receipt.v1.json`
- Comparison Packet: `receipt_comparison.v1.json`

## Public Contract

- package name: `blkbx-lab`
- CLI: `blkbx-lab`
- Python namespace: `blkbx_lab`
- canonical demo result: `InkReceiptResult`

## Current Scope

- The bundled adapter registry ships with `qwen35`.
- Registered adapter names are canonical, and shipped Qwen selectors such as `qwen3.5` and `Qwen/Qwen3.5-2B` resolve to `qwen35`.
- The Qwen3.5 claims demo is the installed teaching path.
- `report()` renders `release-summary` and `comparison-summary` views from the current Ink artifacts.
- Deprecated compatibility shims remain for migration only.

## Current Limits

- `compare()` accepts manifest targets only when a sibling `ink_receipt.v1.json` already exists.
- Production signing keys are not part of this release surface.
- The public docs do not promise a real-model replay workflow through the `blkbx_lab` facade.
- Legacy MAIR and BLT histories remain in-repo for research and migration context, not as first-class public release surfaces.
