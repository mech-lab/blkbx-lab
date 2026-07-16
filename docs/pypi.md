# BLKBX Lab

Open-source Ink Receipt gates for accountable AI agents.

`BLKBX Lab` wraps agent actions with local policy gates and emits signed artifacts that another engineer can verify offline. The current public surface keeps the root receipt runtime intact, ships the installed `qwen35` deterministic demo, and now carries the stable `blkbxs`, `mand8`, and `due` Python APIs through the same `mechlab-sdk` wheel.

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

## Quickstart

```bash
blkbx-lab demo qwen35 --output-dir artifacts/blkbx-lab-demo
blkbx-lab verify artifacts/blkbx-lab-demo/ink_receipt.v2.json
blkbx-lab tamper artifacts/blkbx-lab-demo/ink_receipt.v2.json
blkbx-lab verify artifacts/blkbx-lab-demo/ink_receipt.tampered.v2.json
```

```bash
mechlab demo qwen35 --output-dir artifacts/blkbx-lab-demo
mechlab verify artifacts/blkbx-lab-demo/ink_receipt.v2.json
mechlab tamper artifacts/blkbx-lab-demo/ink_receipt.v2.json
mechlab verify artifacts/blkbx-lab-demo/ink_receipt.tampered.v2.json
```

```python
import blkbx_lab as bl

result = bl.demo(output_dir="artifacts/blkbx-lab-demo")
print(result.manifest_path)
print(result.receipt_path)
print(bl.verify(result.receipt_path).report)
```

```python
import mech_lab as ml

result = ml.demo(output_dir="artifacts/blkbx-lab-demo")
print(result.manifest_path)
print(result.receipt_path)
print(ml.verify(result.receipt_path).report)
```

```python
import blkbxs
import due
import mand8

print(blkbxs.doctor().report)
print(mand8.receipt.create()["schema"])
print(due.receipt.create()["schema"])
```

## What You Get

- Action Evidence Bundle: `ink_manifest.v2.json`
- Receipt: `ink_receipt.v2.json`
- Comparison Packet: `receipt_comparison.v2.json`
- Stable product imports: `blkbxs`, `mand8`, `due`
- Opt-in namespaces: `blkbx_lab.research`, `blkbx_lab.experimental`

## Public Contract

- package name: `mechlab-sdk`
- CLIs: `blkbx-lab`, `mechlab`
- Python namespaces: `blkbx_lab`, `mech_lab`
- stable product imports: `blkbxs`, `mand8`, `due`
- canonical demo result: `InkReceiptResult`

## Current Scope

- The bundled adapter registry ships with `qwen35`.
- Registered adapter names are canonical, and shipped Qwen selectors such as `qwen3.5` and `Qwen/Qwen3.5-2B` resolve to `qwen35`.
- The `qwen35` deterministic demo is the installed teaching path.
- `blkbxs` is a thin banking-facing facade over the current root receipt runtime.
- `mand8` and `due` expose their market-specific receipt APIs from the same wheel.
- `report()` renders `release-summary` and `comparison-summary` views from the current Ink artifacts.
- Deprecated selector aliases remain for migration only.

## Current Limits

- `compare()` accepts manifest targets only when a sibling `ink_receipt.v2.json` already exists.
- The default demo flow still uses the local demo signer backend, but the host layer now supports config-backed file signing, trust registries, and revocation lists under `INKRECEIPTS_CONFIG_DIR`.
- The public docs do not promise a real-model replay workflow through the `blkbx_lab` facade.
- Research and experimental helpers remain opt-in extras even though their namespaces live under the umbrella runtime.
