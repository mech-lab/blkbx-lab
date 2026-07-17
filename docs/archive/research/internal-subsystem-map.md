# Internal Subsystem Map

> Archived on July 17, 2026. Historical research note, not active source-of-truth documentation.

## `internal/trace`

Role:

- action capture and manifest inputs
- preserved legacy trace history under `legacy_blt`
- CLI-facing evidence generation support

Key paths:

- `internal/trace/`
- `internal/trace/legacy_blt/`
- `internal/trace/legacy_blt/src/blt/`

## `internal/ink`

Role:

- public Ink schemas and canonical filenames
- manifest writing
- receipt signing and verification
- preserved legacy MAIR history under `legacy_mair`

Key paths:

- `internal/ink/`
- `internal/ink/schemas/`
- `internal/ink/legacy_mair/`

## `internal/gates`

Role:

- gate policy evaluation
- gate decision reasons
- receipt decision inputs

## `hybrid_mechlab`

Role:

- research and compatibility namespace retained in-repo
- topology and offline analysis helpers
- experimental geometry and `holonom` risk helpers
- Rust bridge shims and version coordination

## `legacy/`

Contents:

- `legacy/hybrid-mechlab-python/`: older Python package surface kept for migration reference
- `legacy/python-rust/`: older Rust companion packaging kept for migration reference
