# Reproducibility Guide

This guide covers the shipped BLKBX Lab release surface and the native verifier toolchain behind it.

## Toolchain

- pinned Rust toolchain: [`rust-toolchain.toml`](rust-toolchain.toml)
- locked workspace dependencies: [`Cargo.lock`](Cargo.lock)
- Python package source: [`pyproject.toml`](pyproject.toml)

## Public-Contract Verification

Run the focused release-facing checks:

```bash
python3 scripts/check_release_readiness.py --skip-clean-worktree
python3 -m pytest -q \
  tests/test_readme_example.py \
  tests/test_packaging_contracts.py \
  tests/test_release_readiness.py
```

## Native Verification Steps

```bash
cargo check
cargo test -p ink-core -p ink-verify -p ink-vectors -p ink-receipt-v2
```

## Demo Artifact Reproduction

```bash
blkbx-lab demo qwen35 --output-dir artifacts/qwen35
blkbx-lab verify artifacts/qwen35/ink_receipt.v2.json
blkbx-lab tamper artifacts/qwen35/ink_receipt.v2.json
blkbx-lab verify artifacts/qwen35/ink_receipt.tampered.v2.json
```

The resulting public artifacts are:

- `ink_manifest.v2.json`
- `ink_receipt.v2.json`
- `ink_receipt.tampered.v2.json`

## Supply-Chain Discipline

- Build release candidates from a clean checkout at a tagged commit.
- Keep release-facing docs aligned with the shipped package and artifact contract.
- Record tool versions, artifact checksums, and validation outputs for tagged releases.
