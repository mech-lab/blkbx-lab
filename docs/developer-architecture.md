# Developer Architecture

## Public entrypoints

- `mech_lab/` is the release-facing SDK and CLI package.
- `mechlab` is the only supported public CLI entrypoint.
- `hybrid_mechlab/` remains in-repo for compatibility and topology/runtime helpers, but it is not the primary release identity.

## Unified repo layout

- `mech_lab/`: public facade, public objects, rendering, CLI wiring
- `hybrid_mechlab/`: compatibility layer and topology/runtime helpers used by the facade
- `internal/blt/`: imported BLT history plus current working-tree snapshot
- `internal/mair/`: imported MAIR history plus current working-tree snapshot
- `legacy/hybrid-mechlab-python/`: legacy Python-only package surface kept for transition work
- `legacy/python-rust/`: legacy Rust companion packaging kept for transition work
- `docs/`, `specs/`, `rust/`: repo-wide documentation and native code

## Import resolution

`mech_lab._workspace` prefers the bundled internal subsystems:

1. repo root
2. `internal/mair/src`
3. `internal/blt/src`
4. legacy sibling repo fallbacks, if present outside the unified repo

That keeps local source checkouts runnable without publishing BLT or MAIR separately while still allowing transitional workstation layouts during migration.

## Runtime flow

1. `mechlab` or `mech_lab` normalizes the public request into a MAIR-backed workflow.
2. `internal/blt` captures or replays traces and exports MAIR-native artifacts.
3. `internal/mair` validates manifests, hydrates bundles, and writes receipts.
4. `hybrid_mechlab` provides offline topology and compatibility helpers used by comparison, analysis, and reporting paths.

## Release rule

Only the root `mechlab-sdk` distribution is published from this repo. Internal subsystem changes are released through that package and should not be documented as independent public deliverables.
