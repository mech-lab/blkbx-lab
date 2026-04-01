# Internal Subsystem Map

## `internal/blt`

Role:

- trace capture and replay
- native Qwen preflight
- analysis export into MAIR artifacts
- grouped CLT and topology summary generation

Key paths:

- `internal/blt/src/blt/`
- `internal/blt/configs/`
- `internal/blt/tests/`

## `internal/mair`

Role:

- artifact schemas and canonical filenames
- manifest writing and hydration
- artifact validation
- release and replay gating

Key paths:

- `internal/mair/src/mair/`
- `internal/mair/schemas/`
- `internal/mair/tests/`

## `hybrid_mechlab`

Role:

- compatibility namespace retained during transition
- MAIR integration helpers
- topology and offline analysis helpers
- Rust bridge shims and version coordination

## `legacy/`

Contents:

- `legacy/hybrid-mechlab-python/`: older Python package surface kept for migration reference
- `legacy/python-rust/`: older Rust companion packaging kept for migration reference

These trees remain in-repo but are outside the first public release surface.
