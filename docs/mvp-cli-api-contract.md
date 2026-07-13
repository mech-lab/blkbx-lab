# BLKBX Lab CLI and API Contract

Release-facing identity:

- repository and product name: `blkbx-lab`
- published package name: `blkbx-lab`
- CLI name: `blkbx-lab`
- Python import path: `blkbx_lab`

## Public Verbs

| CLI | Python | Input | Output |
| --- | --- | --- | --- |
| `blkbx-lab demo` | `bl.demo()` | optional demo name and output dir | `InkReceiptResult` backed by `ink_manifest.v1.json` and `ink_receipt.v1.json` |
| `blkbx-lab doctor` | `bl.doctor()` | none | `DoctorResult` |
| `blkbx-lab trace` | `bl.trace()` | prompt plus optional output dir, trace id, backend, family, model, profile | `ActionEvidenceBundle` backed by `ink_manifest.v1.json` |
| `blkbx-lab analyze` | `bl.analyze()` | manifest path plus optional output dir/profile | `GateAnalysisResult` |
| `blkbx-lab compare` | `bl.compare()` | two receipt targets, or manifest targets that already have sibling receipts, plus optional output dir | `ReceiptComparisonPacket` backed by `receipt_comparison.v1.json` |
| `blkbx-lab gate` | `bl.gate()` | manifest path plus optional policy/profile/output path | `InkReceiptResult` backed by `ink_receipt.v1.json` |
| `blkbx-lab verify` | `bl.verify()` | receipt path | `InkReceiptResult` with verification status |
| `blkbx-lab tamper` | `bl.tamper()` | receipt path | `InkReceiptResult` for the tampered output |
| `blkbx-lab explain` | `bl.explain()` | receipt path | plain-language string |
| `blkbx-lab report` | `bl.report()` | path or public artifact plus optional kind | plain string (`release-summary` or `comparison-summary`; advanced kinds stay experimental) |

## Artifact Mapping

- Action Evidence Bundle -> `ink_manifest.v1.json`
- Receipt -> `ink_receipt.v1.json`
- Comparison Packet -> `receipt_comparison.v1.json`

## Quickstart Commands

```bash
blkbx-lab demo qwen35-claims --output-dir artifacts/qwen35-claims
blkbx-lab verify artifacts/qwen35-claims/ink_receipt.v1.json
blkbx-lab tamper artifacts/qwen35-claims/ink_receipt.v1.json
blkbx-lab verify artifacts/qwen35-claims/ink_receipt.tampered.json
```

```bash
blkbx-lab trace --prompt "Capture a CLI trace." --output-dir artifacts/trace --trace-id trace-cli
blkbx-lab analyze artifacts/trace/ink_manifest.v1.json
blkbx-lab gate artifacts/trace/ink_manifest.v1.json --policy action-gate
blkbx-lab compare --left artifacts/trace/ink_manifest.v1.json --right artifacts/trace/ink_manifest.v1.json --output-dir artifacts/compare
```

## Current Scope

- The installed adapter registry ships with `qwen35`.
- Registered adapter names are canonical, and shipped Qwen aliases resolve to `qwen35`.
- The Qwen3.5 claims demo is the public teaching path.
- `demo()` returns an `InkReceiptResult`, not a separate bundle object.
- `analyze()` currently returns a result object derived from the existing manifest directory; it does not emit a second public artifact file.
- `report()` renders release summaries for manifests and receipts, plus comparison summaries for comparison packets.

## Current Limits

- `compare()` will not synthesize receipts or call `gate()` implicitly for manifest inputs without a sibling receipt.
- The public docs do not promise hook-coverage reports, replay packs, or a real-model replay workflow through `blkbx_lab`.
- Deprecated compatibility shims remain available for migration only.
