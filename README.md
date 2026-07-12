# BLKBX Lab

> Open-source Ink Receipt gates for accountable AI agents.
>
> Qwen3.5 is the installed demo. Receipt gates are the standard.

BLKBX Lab lets developers wrap agent actions with signed, verifiable policy gates. The current public surface ships a Qwen3.5 claims demo, writes Ink artifacts locally, and keeps verification simple enough to inspect from the CLI or Python.

## Install

```bash
pip install --pre blkbx-lab
```

## 60-second quickstart

CLI:

```bash
blkbx-lab demo qwen35-claims --output-dir artifacts/qwen35-claims
blkbx-lab verify artifacts/qwen35-claims/ink_receipt.v1.json
blkbx-lab tamper artifacts/qwen35-claims/ink_receipt.v1.json
blkbx-lab verify artifacts/qwen35-claims/ink_receipt.tampered.json
```

Python:

```python
import blkbx_lab as bl

result = bl.demo(output_dir="artifacts/qwen35-claims")
print(result.manifest_path)
print(result.receipt_path)
print(bl.verify(result.receipt_path).report)
```

## What You Get

- Action Evidence Bundle: `ink_manifest.v1.json` plus the run artifacts for the action proposal.
- Receipt: `ink_receipt.v1.json` for the gate decision.
- Comparison Packet: `receipt_comparison.v1.json` for left/right receipt comparisons.

## Public Contract

- Package: `blkbx-lab`
- CLI: `blkbx-lab`
- Python namespace: `blkbx_lab`
- `demo()` returns `InkReceiptResult`
- `trace()` returns `ActionEvidenceBundle`
- `analyze()` returns `GateAnalysisResult`
- `compare()` returns `ReceiptComparisonPacket`

## How It Works

```text
blkbx-lab CLI / blkbx_lab SDK
        |
        +-- blkbx_lab/      public API, CLI entrypoints, public result objects
        |
        +-- internal/trace  action proposal capture and preserved trace history
        |
        +-- internal/ink    manifests, canonicalization, signing, verification
        |
        +-- internal/gates  policy evaluation and receipt issuance
        |
        +-- adapters/       installed adapter registry (ships with qwen35)
```

## Docs

- [CLI and API contract](docs/mvp-cli-api-contract.md)
- [Public object spec](docs/public-object-spec.md)
- [Developer architecture](docs/developer-architecture.md)
- [Migration and compatibility](docs/migration-compatibility.md)
- [Qwen3.5 validation report](docs/research/qwen35-validation-report.md)

## Current Limits

- The public surface ships the installed `qwen35` adapter and Qwen3.5 claims demo, not a full multi-runtime adapter matrix.
- `report()` currently returns a minimal string summary.
- Receipts are signed with the built-in demo key. Production signing is not part of this release surface.
- Deprecated compatibility shims remain for migration only.
