# Supply-Chain Notes

The INK Receipts kernel release process expects:

- a pinned Rust toolchain
- a committed `Cargo.lock`
- dependency review via `deny.toml`
- deterministic kernel vector checks before release

The current repository posture is local-first. It does not yet include a full signed binary provenance pipeline.
