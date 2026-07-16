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
blkbx-lab verify artifacts/blkbx-lab-demo/ink_receipt.v2.json
blkbx-lab tamper artifacts/blkbx-lab-demo/ink_receipt.v2.json
blkbx-lab verify artifacts/blkbx-lab-demo/ink_receipt.tampered.v2.json
```

```python
import blkbx_lab as bl

result = bl.demo(output_dir="artifacts/blkbx-lab-demo")
print(result.manifest_path)
print(result.receipt_path)
print(bl.verify(result.receipt_path).report)
```

## What You Get

- Action Evidence Bundle: `ink_manifest.v2.json`
- Receipt: `ink_receipt.v2.json`
- Comparison Packet: `receipt_comparison.v2.json`

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
- Deprecated selector aliases remain for migration only.

## Current Limits

- `compare()` accepts manifest targets only when a sibling `ink_receipt.v2.json` already exists.
- The default demo flow still uses the local demo signer backend, but the host layer now supports config-backed file signing, trust registries, and revocation lists under `INKRECEIPTS_CONFIG_DIR`.
- The public docs do not promise a real-model replay workflow through the `blkbx_lab` facade.
- Research histories are intentionally out of this product repo rather than mixed into the shipped source tree.
