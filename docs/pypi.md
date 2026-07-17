# BLKBX Lab Package Surface

This page summarizes the shipped install surface for the root `mechlab-sdk` distribution.

## Install

```bash
pip install --pre mechlab-sdk
```

Optional extras:

```bash
pip install --pre "mechlab-sdk[research]"
pip install --pre "mechlab-sdk[experimental]"
pip install --pre "mechlab-sdk[all]"
```

## Primary Quickstart

```bash
blkbx-lab demo qwen35 --output-dir artifacts/blkbx-lab-demo
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

- Install package: `mechlab-sdk`
- Primary CLI: `blkbx-lab`
- Primary Python namespace: `blkbx_lab`
- Stable product imports: `blkbxs`, `mand8`, `due`
- Public artifacts: `ink_manifest.v2.json`, `ink_receipt.v2.json`, `receipt_comparison.v2.json`

## Current Scope

- The shipped adapter registry exposes the bundled `qwen35` deterministic demo.
- `blkbxs`, `mand8`, and `due` ride in the same root wheel.
- `report()` supports `release-summary` and `comparison-summary` for current public artifacts.
- `blkbx_lab.research` and `blkbx_lab.experimental` remain opt-in extras.

## Current Limits

- The public docs do not promise a real-model replay workflow through `blkbx_lab`.
- `products/*` remain in-repo source slices rather than separate published packages.
- `web/rails` and `packages/ink-ts-verify` remain non-shipping scaffolds.

See the [docs hub](README.md) for the full reference set.
