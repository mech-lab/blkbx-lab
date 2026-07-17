# BLKBX Lab

Open-source Ink Receipt gates for accountable AI agents.

BLKBX Lab ships a small, inspectable receipt flow for high-assurance AI work. Install the root `mechlab-sdk` wheel, run the bundled `qwen35` deterministic demo through `blkbx-lab`, and verify the resulting Ink artifacts locally.

Primary documentation lives in [the docs hub](docs/README.md). Compatibility aliases and historical naming are isolated to the [migration guide](docs/migration-from-mech-lab.md).

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
blkbx-lab demo qwen35 --output-dir artifacts/qwen35
blkbx-lab verify artifacts/qwen35/ink_receipt.v2.json
blkbx-lab tamper artifacts/qwen35/ink_receipt.v2.json
blkbx-lab verify artifacts/qwen35/ink_receipt.tampered.v2.json
```

```python
import blkbx_lab as bl

result = bl.demo(output_dir="artifacts/qwen35")
print(result.manifest_path)
print(result.receipt_path)
print(bl.verify(result.receipt_path).report)
```

## Shipped Surface

- Install package: `mechlab-sdk`
- Primary CLI: `blkbx-lab`
- Primary Python namespace: `blkbx_lab`
- Stable product imports from the same wheel: `blkbxs`, `mand8`, `due`
- Public artifacts: `ink_manifest.v2.json`, `ink_receipt.v2.json`, `receipt_comparison.v2.json`

## Repo Map

```text
blkbx-lab/
  python/blkbx_lab/               primary CLI and Python surface
  python/blkbxs/                  banking-facing facade
  python/mand8/                   insurance-facing facade
  python/due/                     legal-facing facade
  rust/crates/ink-core/           domain-neutral trust waist
  rust/crates/ink-host/           std host adapter and v2 compatibility layer
  rust/crates/ink-verify/         native verification primitives
  rust/crates/ink-cli/            kernel-facing verifier CLI
  rust/crates/ink-tui/            zero-JS terminal verifier
  rust/crates/ink-receipt-v2/     current v2 receipt and bundle verifier surface
  packages/ink-ts-verify/         in-repo TypeScript verifier scaffold
  web/rails/                      in-repo portal scaffold
  web/verify/                     static verifier scaffold
  products/                       in-repo source slices for sibling products
  docs/                           source-of-truth documentation hub and archive
```

## Docs

- [Docs hub](docs/README.md)
- [Install and package surface](docs/pypi.md)
- [CLI and API contract](docs/mvp-cli-api-contract.md)
- [Public object spec](docs/public-object-spec.md)
- [Developer architecture](docs/developer-architecture.md)
- [Product architecture](docs/product-architecture.md)
- [Migration and compatibility](docs/migration-compatibility.md)
- [Validation evidence](docs/research/qwen35-validation-report.md)

## Current Limits

- The public adapter registry still ships only the bundled `qwen35` deterministic demo.
- `compare()` requires sibling `ink_receipt.v2.json` artifacts when manifest paths are used as inputs.
- `products/*`, `web/rails`, and `packages/ink-ts-verify` remain in-repo source or scaffold surfaces, not separate published artifacts.
