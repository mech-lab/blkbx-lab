# BLKBX Lab CLI and API Contract

This page describes the shipped public contract for the root `mechlab-sdk` wheel.

## Release-Facing Identity

- install package: `mechlab-sdk`
- primary CLI: `blkbx-lab`
- primary Python namespace: `blkbx_lab`
- stable product imports: `blkbxs`, `mand8`, `due`

Compatibility aliases are documented separately in the [migration notes](migration-compatibility.md).

## Public Verbs

| CLI | Python | Input | Output |
| --- | --- | --- | --- |
| `blkbx-lab demo` | `bl.demo()` | optional demo name and output dir | `InkReceiptResult` backed by `ink_manifest.v2.json` and `ink_receipt.v2.json` |
| `blkbx-lab doctor` | `bl.doctor()` | optional local issuer initialization flag | `DoctorResult` |
| `blkbx-lab trace` | `bl.trace()` | prompt plus optional output dir, trace id, and adapter selector | `ActionEvidenceBundle` backed by `ink_manifest.v2.json` |
| `blkbx-lab analyze` | `bl.analyze()` | manifest path plus optional policy, controls, output dir, and profile | `GateAnalysisResult` |
| `blkbx-lab gate` | `bl.gate()` | manifest path plus optional policy, controls, output path, profile, and `demo_signer` | `InkReceiptResult` backed by `ink_receipt.v2.json` |
| `blkbx-lab verify` | `bl.verify()` | receipt path plus optional manifest path | `InkReceiptResult` with verification status |
| `blkbx-lab compare` | `bl.compare()` | two receipt targets, or manifest targets that already have sibling receipts, plus optional output dir | `ReceiptComparisonPacket` backed by `receipt_comparison.v2.json` |
| `blkbx-lab tamper` | `bl.tamper()` | receipt path | `InkReceiptResult` for the tampered output |
| `blkbx-lab explain` | `bl.explain()` | receipt path | plain-language string |
| `blkbx-lab report` | `bl.report()` | path or public artifact plus optional kind | plain string |

## Artifact Mapping

- Action Evidence Bundle -> `ink_manifest.v2.json`
- Receipt -> `ink_receipt.v2.json`
- Comparison Packet -> `receipt_comparison.v2.json`

## Canonical Quickstart

```bash
blkbx-lab demo qwen35 --output-dir artifacts/qwen35
blkbx-lab verify artifacts/qwen35/ink_receipt.v2.json
blkbx-lab tamper artifacts/qwen35/ink_receipt.v2.json
blkbx-lab verify artifacts/qwen35/ink_receipt.tampered.v2.json
```

```bash
blkbx-lab trace --prompt "Capture a CLI trace." --adapter qwen35 --output-dir artifacts/trace --trace-id trace-cli
blkbx-lab analyze artifacts/trace/ink_manifest.v2.json --output-dir artifacts/trace
blkbx-lab gate artifacts/trace/ink_manifest.v2.json --demo-signer
blkbx-lab compare --left artifacts/trace/ink_manifest.v2.json --right artifacts/trace/ink_manifest.v2.json --output-dir artifacts/compare
blkbx-lab report artifacts/trace/ink_manifest.v2.json --kind release-summary
```

## Current Scope

- The installed public teaching path is the bundled `qwen35` deterministic demo.
- Deprecated selector aliases such as `qwen35-claims`, `qwen3.5`, and `Qwen/Qwen3.5-2B` normalize to `qwen35`.
- `demo()` returns an `InkReceiptResult`.
- `analyze()` reads the existing manifest directory and does not emit a second public artifact file.
- `report()` renders current public artifact summaries rather than experimental research views.

## Current Limits

- `compare()` does not synthesize receipts for manifest inputs without sibling `ink_receipt.v2.json` files.
- Unsupported adapter, family, model, backend, and profile combinations fail loudly.
- The public docs do not promise multi-runtime adapter coverage through the primary facade.
