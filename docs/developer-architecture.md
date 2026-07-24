# Developer Architecture

BLKBX Lab ships a layered runtime with a small public Python surface over a native Rust trust waist.

## Current Stack

```text
mechlab-sdk install
        |
        +-- python/blkbx_lab/       primary CLI parser, Python API, public result objects
        |
        +-- python/blkbxs/          banking-facing facade from the same wheel
        |   +-- schema/ubr/graph/
        |       bundle/scenarios    BLKBXS UBR helpers and generated fixture access
        +-- python/mand8/           insurance-facing facade from the same wheel
        +-- python/due/             legal-facing facade from the same wheel
        |
        +-- rust/crates/ink-py/     PyO3 bridge exposed as blkbx_lab._ink_native
        +-- rust/crates/ink-host/   std host adapter for current v2 issuance and verification
        +-- rust/crates/ink-core/   domain-neutral trust waist
        +-- rust/crates/ink-verify/ verification primitives
        +-- rust/crates/ink-receipt-v2/ current receipt and bundle verifier surface
        |
        +-- policies/ schemas/      shipped policy and schema assets
        +-- docs/                   source-of-truth docs and archive
```

## Public Facade

`python/blkbx_lab/` owns the primary shipped surface:

- `blkbx-lab` CLI
- `blkbx_lab` Python API
- public result objects documented in [the object spec](public-object-spec.md)

## Host and Kernel Split

- `ink-host` owns the current public `v2` artifact issuance and verification path.
- `ink-core` holds the domain-neutral receipt semantics beneath that host layer.
- `ink-verify` adds verification logic without redefining the Python or JSON surface.

## Product Layers

BLKBXS, MAND8, and DUE sit above the shared receipt runtime:

- `BLKBXS`: bankability and verification-facing banking evidence
- `MAND8`: insurance and delegated-authority evidence
- `DUE`: legal defensibility evidence

Those layers add domain framing and bundle semantics without changing the shared trust waist.

BLKBXS UBR adds a banking event graph on top of the shared receipt runtime. Python exposes schema loading, event creation, graph validation, bundle export, and the generated SMB loan fixture through `blkbxs`. Rails exposes UBR receipt creation, graph bundling, dashboards, and verifier artifacts under `/api/v1/blkbxs/*`.

For UBR, the domain JSON stays in `body_json`. The authoritative cryptographic artifact is the linked `ink.receipt.v2` portable receipt. Rails UBR creation requires hosted issuer configuration and rolls back on unsigned output.
