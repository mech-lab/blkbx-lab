# Reproducibility Guide

## Toolchain

- pinned toolchain: `rustc 1.94.1`
- toolchain file: [`rust-toolchain.toml`](rust-toolchain.toml)
- locked dependencies: `Cargo.lock`

## Local Verification Steps

```bash
cargo check
cargo test -p ink-core -p ink-verify -p ink-vectors
```

## Supply-Chain Discipline

- dependency policy file: [`deny.toml`](deny.toml)
- workspace lockfile is required for release builds
- release binaries should be built from a clean checkout at a tagged commit

## Deterministic Vector Discipline

The v1 kernel test surface uses `ink-vectors` to ensure:

- the same logical receipt emits the same canonical bytes
- canonical bytes decode back into the same receipt envelope
- receipt verification outcomes are stable across runs

## Release Artifact Checks

For release candidates, publish:

- commit or tag identifier
- `cargo --version`
- `rustc --version`
- checksums for the generated CLI and WASM verifier artifacts
