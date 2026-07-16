# BLKBX Lab

Open-source Ink Receipt gates for accountable AI agents.

`qwen35` is the installed deterministic demo. Receipt gates are the standard.

Black Box Labs builds receipt-native infrastructure for high-assurance AI.

> INK Receipts are the proof primitive. BLKBXS applies them to banking. MAND8 applies them to insurance. DUE applies them to legal defensibility.

## Sibling Product Slices

This repository now carries sibling product slices under the Black Box Labs umbrella:

- `BLKBXS SDK`: the current root OSS receipt surface
- `MAND8 SDK`: insurance-facing receipts and evidence bundles
- `DUE SDK`: legal-facing defensibility receipts and evidence bundles

MAND8 and DUE are siblings. DUE is not buried inside MAND8.

MAND8 is UK-first by design. Its delegated-authority framing starts with the Lloyd's and London market workflow rather than treating the UK as a later localization pass.

## Current Shipped Surface

Black Box Labs is the product brand. `mechlab-sdk` is the current PyPI install target for `v0.9.1`. A plain install carries the current root runtime plus stable `blkbxs`, `mand8`, and `due` Python APIs. Both `blkbx-lab` and `mechlab` CLIs are available, and both `blkbx_lab` and `mech_lab` imports remain available.

```bash
pip install --pre mechlab-sdk
```

Opt-in extras:

```bash
pip install --pre "mechlab-sdk[research]"
pip install --pre "mechlab-sdk[experimental]"
pip install --pre "mechlab-sdk[all]"
```

```bash
blkbx-lab demo qwen35 --output-dir artifacts/qwen35
blkbx-lab verify artifacts/qwen35/ink_receipt.v2.json
blkbx-lab tamper artifacts/qwen35/ink_receipt.v2.json
blkbx-lab verify artifacts/qwen35/ink_receipt.tampered.v2.json
```

```bash
mechlab demo qwen35 --output-dir artifacts/qwen35
mechlab verify artifacts/qwen35/ink_receipt.v2.json
mechlab tamper artifacts/qwen35/ink_receipt.v2.json
mechlab verify artifacts/qwen35/ink_receipt.tampered.v2.json
```

Python:

```python
import blkbx_lab as bl

result = bl.demo(output_dir="artifacts/qwen35")
print(result.manifest_path)
print(result.receipt_path)
print(bl.verify(result.receipt_path).report)
```

```python
import mech_lab as ml

result = ml.demo(output_dir="artifacts/qwen35")
print(result.manifest_path)
print(result.receipt_path)
print(ml.verify(result.receipt_path).report)
```

Product APIs from the same install:

```python
import blkbxs
import due
import mand8

print(blkbxs.doctor().report)
print(mand8.receipt.create()["schema"])
print(due.receipt.create()["schema"])
```

## Repo Map

```text
blkbx-lab/
  python/blkbx_lab/               shared runtime and umbrella namespaces
  python/blkbxs/                  banking-facing public facade
  python/mand8/                   insurance-facing public facade
  python/due/                     legal-facing public facade
  rust/crates/ink-core/           receipt core
  rust/crates/ink-host/           host/runtime verification
  rust/crates/ink-py/             PyO3 bridge
  products/
    mand8-sdk/                    insurance-facing source slice
    due-sdk/                      legal-facing source slice
```

The slice directories remain source slices and repo organization units. The shipped pip artifact is `mechlab-sdk`, and its stable wheel surface now carries the `blkbxs`, `mand8`, and `due` Python packages directly.

## Docs

- [CLI and API contract](docs/mvp-cli-api-contract.md)
- [Public object spec](docs/public-object-spec.md)
- [Developer architecture](docs/developer-architecture.md)
- [Migration and compatibility](docs/migration-compatibility.md)
- [Product architecture](docs/product-architecture.md)
- [Brand architecture](docs/brand-architecture.md)
- [Receipt domain model](docs/receipt-domain-model.md)
- [Qwen3.5 validation report](docs/research/qwen35-validation-report.md)

## Current Limits

- The root public surface still ships the installed `qwen35` deterministic demo rather than a full multi-runtime adapter matrix.
- The new MAND8 and DUE slices use stub integrity adapters, not heavy cryptography or production signer infrastructure.
- Research and experimental helpers live under `blkbx_lab.research` and `blkbx_lab.experimental`, but the supported dependency path for them is still opt-in extras.
- Shared `packages/*` primitives are part of the target architecture, but this pass does not migrate the current root runtime into that structure.
- `products/*` remain in-repo slices under the Black Box Labs umbrella rather than separate published PyPI artifacts.
