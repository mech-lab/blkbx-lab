# mech-lab CLI and API Contract

Release-facing identity:

- repository and package name: `mech-lab`
- CLI name: `mechlab`
- Python import path: `mech_lab`
- internal subsystems: `internal/blt` and `internal/mair`

## Public verbs

| CLI | Python | Input | Output |
| --- | --- | --- | --- |
| `mechlab demo` | `ml.demo()` | optional prompt/output dir | `AnalysisResult` backed by `mair_manifest.v1.json` and `assurance_receipt.v1.json` |
| `mechlab doctor` | `ml.doctor()` | none | `DoctorResult` describing local readiness |
| `mechlab trace` | `ml.trace()` | prompt plus optional family/model/backend/profile | `EvidenceBundle` backed by `mair_manifest.v1.json` |
| `mechlab analyze` | `ml.analyze()` | one bundle/manifest | `AnalysisResult` backed by an updated `mair_manifest.v1.json` |
| `mechlab compare` | `ml.compare()` | two bundles/manifests | `ComparisonPacket` backed by `backend_comparison.v1.json` |
| `mechlab gate` | `ml.gate()` | one bundle/manifest plus policy/profile | `ReceiptResult` backed by `assurance_receipt.v1.json` |
| `mechlab explain` | `ml.explain()` | one receipt/bundle | plain-language string |
| `mechlab report` | `ml.report()` | one bundle/receipt/comparison packet plus optional kind | rendered string |

## Artifact mapping lock

- Evidence Bundle -> `mair_manifest.v1.json` plus required MAIR artifacts
- Receipt -> `assurance_receipt.v1.json`
- Replay Pack -> analyzed/intervention-enriched MAIR bundle
- Comparison Packet -> `backend_comparison.v1.json`

Hard rule:
- no product-specific disk schema
- no raw BLT-native structures in the public API

## Qwen3.5 product lane

Status:
- native `qwen3_5` runtime proof is complete through the public `mechlab` façade
- the validated real-model rerun is documented in [qwen35-validation-report.md](qwen35-validation-report.md)
- the successful host-local rerun on April 1, 2026 used a public CPU override profile after `device:auto` failed on the `16 GiB` arm64/MPS machine used for validation

Product command:

```bash
mechlab trace --family qwen3.5 --model qwen3.5-2b --prompt "Measure the 3:1 tract bridge rhythm."
```

Product analysis profile:

```bash
mechlab analyze run/mair_manifest.v1.json --profile qwen3.5-hybrid
```

Required hooks:
- `pre-D1`
- `post-D1`
- `post-D2`
- `post-D3`
- `post-attention`
- `block-output`

Report kinds:
- `bridge-necessity`
- `compression-forgetting`
- `tract-vs-bridge`
- `release-summary`
- `comparison-summary`

Current CLI follow-up:
- `mechlab gate --profile qwen3.5-hybrid` is not yet normalized with the named public profile vocabulary used by `analyze`; use `mechlab gate <manifest> --policy release-assurance` until that semantics bug is fixed
