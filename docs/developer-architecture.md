# Developer Architecture

BLKBX Lab now has two Rust layers with a deliberate split:

```text
blkbx-lab CLI / blkbx_lab SDK
        |
        +-- python/blkbx_lab/       public API, CLI parser, packaged adapters, result objects
        |
        +-- rust/crates/ink-py/     PyO3 bridge exposed as blkbx_lab._ink_native
        |
        +-- rust/crates/ink-host/   std adapter, manifest IO, signer config, v2 compatibility
        |
        +-- rust/crates/ink-core/   domain-neutral no_std kernel
        |       |
        |       +-- rust/crates/ink-verify/   optional no_std attestation verification
        |       +-- rust/crates/ink-vectors/  deterministic kernel vectors
        |       +-- rust/crates/ink-cli/      local kernel CLI
        |       +-- rust/crates/ink-wasm/     portable verifier target
        |
        +-- policies/ schemas/      shipped policy and schema assets
        |
        +-- tests/ docs/            product-facing verification and documentation
```

## Public Facade

`python/blkbx_lab/` remains the release-facing SDK and CLI surface for the shipped umbrella wheel.

## Kernel Layer

`rust/crates/ink-core/` is now the kernel trust waist:

- `no_std`
- safe Rust
- deterministic receipt envelope
- canonical encoding
- hash commitments
- replay and compare semantics
- bundle validation

This layer is domain-neutral. It does not own banking, insurance, or legal semantics.

## Verification Layer

`rust/crates/ink-verify/` adds optional signature verification over kernel receipts without moving private-key operations into the kernel.

## Compatibility Layer

`rust/crates/ink-host/` remains the `std` adapter that:

- creates and reads the current `ink.manifest.v2`
- issues and verifies the current `ink.receipt.v2`
- projects current v2 receipts into the neutral kernel envelope during verification
- verifies historical encodings
- loads signer config, trust registries, and revocation data

The current shipped v2 receipt path is intentionally a host-level compatibility surface above the new kernel.

## Product Layers

BLKBXS, MAND8, and DUE remain above the kernel:

- `BLKBXS`: bankability evidence
- `MAND8`: insurability evidence
- `DUE`: legal defensibility evidence

They bind schemas and compose artifacts. They do not redefine the kernel semantics.
