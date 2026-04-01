# mech-lab

> Mechanistic interpretability that ships: generate evidence bundles, receipts, and comparison packets fast enough for real engineering workflows.

`mech-lab` is the public façade over two internal layers:
- `BLT` captures and replays hybrid traces.
- `MAIR` is the canonical on-disk artifact and validation contract.

## 60-second demo

```bash
pip install mech-lab
mechlab demo
```

Current workspace note:
- in this repo, `mechlab demo` works automatically when the sibling `BLT` and `MAIR` repos are present
- the façade, object model, and CLI are now productized here; publishing the full one-package runtime remains a release-packaging follow-on

Workspace hygiene:
- generated caches and local build outputs under this tree are disposable
- the standalone `/Volumes/128/BLT` repo and the nested `/Volumes/128/hybridTDA/BLT` repo are not auto-synced
- this cleanup pass does not settle the tracked `src/*.egg-info` policy in the standalone BLT and MAIR repos

Outputs:
- `mair_manifest.v1.json` for the Evidence Bundle
- `assurance_receipt.v1.json` for the release decision
- `topology_summary.v1.json`, `offline_topology_report.v1.json`, and grouped CLT artifacts for analysis

## Why this exists

AI platform teams do not pay for topology tooling in the abstract. They pay when interpretability work becomes a release decision, a model comparison packet, or an incident replay artifact that other people can verify offline.

`mech-lab` keeps the public surface simple while preserving the existing runtime and artifact stack underneath.

## Choose your path

- I want a first win: [Demo](#60-second-demo) / [Quickstart](#quickstart)
- I want the product verbs: [CLI](#cli) / [Python](#python)
- I want the contract: [Artifacts](#artifacts) / [Docs](#docs)
- I want the real model lane: [Qwen3.5](#qwen35-lane)

## What this is / isn't

- Is: a façade-first SDK and CLI for Evidence Bundles, Receipts, Replay Packs, and Comparison Packets
- Is: an orchestration layer over BLT runtime capture and MAIR artifact validation
- Isn't: a second persisted artifact format
- Isn't: a BLT-first public UX
- Isn't: a requirement to ship learned sheaf/cohomology machinery in the MVP

## Quickstart

```python
import mech_lab as ml

bundle = ml.demo(output_dir="artifacts/mechlab-demo")
print(bundle.manifest_path)
print(ml.report(bundle))
```

## CLI

```bash
mechlab demo
mechlab doctor
mechlab trace --prompt "Map bridge dependence." --backend mock
mechlab analyze artifacts/mechlab-demo/mair_manifest.v1.json --profile qwen3.5-hybrid
mechlab compare --left run-a/mair_manifest.v1.json --right run-b/mair_manifest.v1.json
mechlab gate artifacts/mechlab-demo/mair_manifest.v1.json --policy release-assurance
mechlab explain artifacts/mechlab-demo/assurance_receipt.v1.json
mechlab report artifacts/mechlab-demo/mair_manifest.v1.json --kind release-summary
```

## Python

```python
import mech_lab as ml

bundle = ml.trace(
    "Measure bridge necessity for this prompt.",
    backend="mock",
    trace_id="trace-sdk-docs",
)
analysis = ml.analyze(bundle, profile="qwen3.5-hybrid")
packet = ml.compare(left=analysis, right=analysis)
receipt = ml.gate(analysis, policy="release-assurance")
print(ml.report(packet, kind="comparison-summary"))
print(ml.explain(receipt))
```

## Artifacts

Public product language maps to MAIR directly:
- Evidence Bundle = `mair_manifest.v1.json` + required MAIR artifacts
- Receipt = `assurance_receipt.v1.json`
- Replay Pack = analyzed/intervention-enriched MAIR bundle
- Comparison Packet = `backend_comparison.v1.json`

No product-specific on-disk schema is introduced.

## Qwen3.5 lane

The required real-model MVP lane is `Qwen3.5-2B`.

Validation status:
- native `qwen3_5` runtime proof is complete through the public `mechlab` façade
- the validated runtime root is `/Volumes/2.5SSDDD128/mechlab-qwen35-native`
- on this `16 GiB` arm64/MPS host, the successful public rerun used the documented CPU override profile after `device:auto` failed before artifact emission
- the canonical runtime evidence and artifact paths are recorded in the [Qwen3.5 validation report](/Volumes/128/hybridTDA/docs/qwen35-validation-report.md)

```bash
mechlab trace --family qwen3.5 --model qwen3.5-2b --prompt "Measure the 3:1 tract/bridge rhythm."
mechlab analyze ./mechlab-trace-*/mair_manifest.v1.json --profile qwen3.5-hybrid
mechlab report ./mechlab-trace-*/mair_manifest.v1.json --kind tract-vs-bridge
```

Validated public fallback on this host:

```bash
mechlab trace \
  --family qwen3.5 \
  --model qwen3.5-2b \
  --profile /Volumes/2.5SSDDD128/mechlab-qwen35-native/artifacts/qwen35-cpu.profile.json \
  --prompt "Measure the 3:1 tract/bridge rhythm." \
  --output-dir /Volumes/2.5SSDDD128/mechlab-qwen35-native/artifacts/qwen35-real-run
mechlab analyze /Volumes/2.5SSDDD128/mechlab-qwen35-native/artifacts/qwen35-real-run/mair_manifest.v1.json --profile qwen3.5-hybrid
mechlab report /Volumes/2.5SSDDD128/mechlab-qwen35-native/artifacts/qwen35-real-run/mair_manifest.v1.json --kind tract-vs-bridge
mechlab gate /Volumes/2.5SSDDD128/mechlab-qwen35-native/artifacts/qwen35-real-run/mair_manifest.v1.json --policy release-assurance
```

Required hook coverage for the product lane:
- `pre-D1`
- `post-D1`
- `post-D2`
- `post-D3`
- `post-attention`
- `block-output`

Current follow-up:
- `mechlab gate --profile qwen3.5-hybrid` still has inconsistent profile semantics and is tracked separately from the native-runtime milestone

## Docs

- [CLI/API contract](/Volumes/128/hybridTDA/docs/mvp-cli-api-contract.md)
- [Public object spec](/Volumes/128/hybridTDA/docs/public-object-spec.md)
- [Qwen3.5 validation report](/Volumes/128/hybridTDA/docs/qwen35-validation-report.md)
- [Hybrid schedule spec](/Volumes/128/hybridTDA/specs/hybrid_schedule_v1.md)
- [Sheaf connection spec](/Volumes/128/hybridTDA/specs/sheaf_connection_v1.md)
- [Native core portfolio spec](/Volumes/128/hybridTDA/specs/native_core_portfolio_v1.md)

## Internal continuity

`hybrid_mechlab` remains import-compatible during the transition, but public docs, packaging, and examples all go through `mech_lab` and `mechlab`.
