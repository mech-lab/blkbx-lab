# Developer Architecture

BLKBX Lab is structured into the following layers:

```text
blkbx-lab CLI / blkbx_lab SDK
        |
        +-- python/blkbx_lab/       public API, CLI parser, packaged adapters, result objects
        |
        +-- rust/crates/ink-py/     PyO3 bindings exposed as blkbx_lab._ink_native
        |
        +-- rust/crates/ink-host/   manifest IO, policy evaluation, signer config, trust registry
        |
        +-- rust/crates/ink-core/   no_std receipt core, transcript encodings, digest/signature logic
        |
        +-- policies/ schemas/      shipped policy and schema assets
        |
        +-- tests/ docs/            product-facing verification and documentation
```

## Public Facade (`python/blkbx_lab/`)

This is the canonical SDK and CLI surface. Release-facing docs, examples, and tests should target this layer.

## Python Package (`python/blkbx_lab/`)

This package owns:

- the public `blkbx_lab` namespace
- the installed `qwen35` deterministic demo adapter
- CLI entrypoints and public result objects
- compatibility normalization for deprecated adapter-selection flags

## Host Layer (`rust/crates/ink-host/`)

This crate owns:

- manifest creation and evidence hashing
- policy evaluation and receipt issuance
- signer backend config loading
- trust-registry and revocation-list enforcement
- receipt verification and comparison packet signing

## Core Layer (`rust/crates/ink-core/`)

This crate is the product's trust waist. It stays `no_std` and owns the semantic receipt model plus the signed transcript encoders:

- TLV v2 is the current default signed transcript.
- TLV legacy v1 remains supported for explicit compatibility verification.
- canonical JSON v1 is supported as a governed host-level encoding choice.

## Assets (`policies/`, `schemas/`, `tests/`, `docs/`)

Only shipped product assets remain in this repository. Research trees, compatibility packages, notebooks, and legacy experimental crates are intentionally out of scope for the product repo.

## Repo Boundary

This repository is now the OSS receipt-core/product tree. If historical research material needs to be preserved, it belongs in a separate history-preserving research repo rather than mixed into this install surface.
