# BLKBX Lab

Mechanistic interpretability that ships.

`Architecture-agnostic IR · Sheaf holonomy · SLSA L3 provenance`

`BLKBX Lab` produces Evidence Bundles, Receipts, Replay Packs, and Comparison Packets that other engineers can verify offline. The public trust anchor is concrete: the native Qwen3.5 lane runs through `blkbx-lab` and emits MAIR-backed artifacts.

## Install

```bash
pip install --pre blkbx-lab
```

## Quickstart

```bash
blkbx-lab demo --output-dir artifacts/blkbx-lab-demo
blkbx-lab report artifacts/blkbx-lab-demo/ink_manifest.v1.json --kind release-summary
```

```python
import blkbx_lab as ml

bundle = ml.demo(output_dir="artifacts/blkbx-lab-demo")
print(bundle.manifest_path)
print(ml.report(bundle))
```

## What You Get

- Evidence Bundle: `ink_manifest.v1.json` plus required MAIR-backed run artifacts
- Receipt: `ink_receipt.v1.json`
- Replay Pack: analyzed MAIR bundle with hook validation and intervention outputs
- Comparison Packet: `receipt_comparison.v1.json`

## Real Model Proof

- native `qwen3_5` runtime proof is complete through the public `blkbx-lab` facade
- the validated rerun used the real `Qwen/Qwen3.5-2B` checkpoint
- the validated host-local rerun used a documented CPU override after `device:auto` failed before artifact emission on the recorded machine

## Public Contract

- package name: `blkbx-lab`
- CLI: `blkbx-lab`
- Python namespace: `blkbx_lab`
- disk contract: MAIR-backed artifacts only
