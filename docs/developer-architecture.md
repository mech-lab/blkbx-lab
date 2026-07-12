# Developer Architecture

BLKBX Lab is structured into the following layers:

```text
blkbx-lab CLI / blkbx_lab SDK
        |
        +-- blkbx_lab/              public API, CLI parser, result objects
        |
        +-- internal/trace/         action capture and preserved legacy trace code
        |
        +-- internal/ink/           manifest, canonicalization, signing, verification
        |
        +-- internal/gates/         gate policy evaluation
        |
        +-- adapters/               installed adapter registry (ships with qwen35)
        |
        +-- hybrid_mechlab/         research and compatibility namespace
```

## Public Facade (`blkbx_lab/`)

This is the canonical SDK and CLI surface. Release-facing docs, examples, and tests should target this layer.

## Trace Layer (`internal/trace/`)

This layer captures action proposals and preserves the historical trace subsystem under `internal/trace/legacy_blt/`. It is kept in-repo for continuity, not as a first-class public package.

## Ink Layer (`internal/ink/`)

This layer owns the current public artifact contract:

- `ink_manifest.v1.json`
- `ink_receipt.v1.json`
- `receipt_comparison.v1.json`

The old MAIR implementation remains under `internal/ink/legacy_mair/` for historical context.

## Gates Layer (`internal/gates/`)

This layer evaluates actions against policies and produces gate decisions and receipt content.

## Adapters (`adapters/`)

This layer exposes the thin adapter registry used by the public trace and demo flows. The current installed public adapter is `qwen35`.

## Compatibility Surfaces

- `hybrid_mechlab/` stays in-repo for research and legacy workflows.
- Deprecated compatibility shims delegate to the canonical `blkbx_lab` surface and emit deprecation warnings.
