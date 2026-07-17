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

Black Box Labs is the product brand. `mechlab-sdk` `1.0.0` is the current PyPI install target. A plain install carries the current root runtime plus stable `blkbxs`, `mand8`, and `due` Python APIs. Both `blkbx-lab` and `mechlab` CLIs are available, and both `blkbx_lab` and `mech_lab` imports remain available.

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
  rust/crates/ink-core/           domain-neutral deterministic kernel
  rust/crates/ink-verify/         optional no_std signature verification
  rust/crates/ink-vectors/        deterministic kernel vectors
  rust/crates/ink-cli/            local kernel CLI
  rust/crates/ink-wasm/           portable verifier target
  rust/crates/ink-host/           std adapter and v2 compatibility surface
  rust/crates/ink-py/             PyO3 bridge
  web/rails/                      in-repo workflow portal scaffold, not a shipped verifier surface
  packages/ink-ts-verify/         in-repo TypeScript verifier primitive scaffold
  products/
    mand8-sdk/                    insurance-facing source slice
    due-sdk/                      legal-facing source slice
```

The slice directories remain source slices and repo organization units. The shipped pip artifact is `mechlab-sdk`, and its stable wheel surface now carries the `blkbxs`, `mand8`, and `due` Python packages directly. The Rails and TypeScript directories are in-repo scaffolds and are not part of the published trust boundary or PyPI artifact set.

The root public CLIs remain `blkbx-lab` and `mechlab`. The new `ink` CLI is a kernel-facing verifier tool, not a replacement for the umbrella product CLIs.

## Docs

- [CLI and API contract](docs/mvp-cli-api-contract.md)
- [Public object spec](docs/public-object-spec.md)
- [Developer architecture](docs/developer-architecture.md)
- [Migration and compatibility](docs/migration-compatibility.md)
- [Formal semantics draft](FORMAL_SEMANTICS.md)
- [Reproducibility guide](REPRODUCIBILITY.md)
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
- `web/rails` and `packages/ink-ts-verify` are intentionally non-shipping scaffolds in this release line; the native Rust verifier remains the trust root.
