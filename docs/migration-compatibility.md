# Migration And Compatibility Notes

## Unified repo target

The public GitHub release target is a single repo and package named `mech-lab`.

The unified tree keeps:

- `mech_lab` as the release-facing SDK and CLI
- `internal/blt` and `internal/mair` as bundled subsystem histories
- `hybrid_mechlab` as a compatibility namespace during transition

## History preservation

- BLT history is imported into `internal/blt`.
- MAIR history is imported into `internal/mair`.
- The old embedded `hybridTDA/BLT` git repo is removed from the root tree and replaced by the imported `internal/blt` subtree.

## Legacy surfaces

The following paths are retained for compatibility and migration work only:

- `legacy/hybrid-mechlab-python`
- `legacy/python-rust`

They are not the primary release identity and are not part of the first public publish flow.

## Transitional fallback behavior

`mech_lab._workspace` still recognizes legacy sibling `BLT` and `MAIR` source trees if they exist outside the unified repo. That fallback is for migration safety only; bundled `internal/blt` and `internal/mair` are the canonical layout.

## Qwen runtime note

The native Qwen3.5 runtime proof now belongs to the unified public surface. `qwen3_next` was evaluated only as a structural reference and is not part of the shipped runtime path. See [qwen35-validation-report.md](qwen35-validation-report.md) for the recorded rerun evidence.
