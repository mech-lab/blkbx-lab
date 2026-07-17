# Technical Security Hardening Note

This page covers implementation-level hardening guidance for the current shipped BLKBX Lab surface. It complements the public vulnerability policy in [`../SECURITY.md`](../SECURITY.md).

## Current Hardening Posture

- Rust trust-waist crates are intended to stay safe-Rust-first.
- Verification is designed for local, inspectable, offline operation.
- The host layer supports operator-managed signer configuration, trust registries, and revocation lists.

## Build and Dependency Controls

- use the pinned Rust toolchain from [`../rust-toolchain.toml`](../rust-toolchain.toml)
- keep dependency policy in [`../deny.toml`](../deny.toml)
- validate release candidates with [`../scripts/check_release_readiness.py`](../scripts/check_release_readiness.py) and [`../scripts/check_local_release.py`](../scripts/check_local_release.py)

## Documentation Boundary

- Root [`../SECURITY.md`](../SECURITY.md) is the public reporting policy.
- This document is for technical implementation notes.
- Historical hardening plans now live under [`archive/`](archive/README.md).
