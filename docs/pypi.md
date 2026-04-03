# mech-lab

Mechanistic interpretability that ships.

`Architecture-agnostic IR · Sheaf holonomy · SLSA L3 provenance`

`mech-lab` produces Evidence Bundles, Receipts, Replay Packs, and Comparison Packets that other engineers can verify offline. The public trust anchor is concrete: the native Qwen3.5 lane runs through `mechlab` and emits MAIR-backed artifacts.

## Install

```bash
pip install --pre mech-lab
```

## Quickstart

```bash
mechlab demo --output-dir artifacts/mechlab-demo
mechlab report artifacts/mechlab-demo/mair_manifest.v1.json --kind release-summary
```

```python
import mech_lab as ml

bundle = ml.demo(output_dir="artifacts/mechlab-demo")
print(bundle.manifest_path)
print(ml.report(bundle))
```

## What You Get

- Evidence Bundle: `mair_manifest.v1.json` plus required MAIR-backed run artifacts
- Receipt: `assurance_receipt.v1.json`
- Replay Pack: analyzed MAIR bundle with hook validation and intervention outputs
- Comparison Packet: `backend_comparison.v1.json`

## Real Model Proof

- native `qwen3_5` runtime proof is complete through the public `mechlab` facade
- the validated rerun used the real `Qwen/Qwen3.5-2B` checkpoint
- the validated host-local rerun used a documented CPU override after `device:auto` failed before artifact emission on the recorded machine

## Public Contract

- package name: `mech-lab`
- CLI: `mechlab`
- Python namespace: `mech_lab`
- disk contract: MAIR-backed artifacts only
