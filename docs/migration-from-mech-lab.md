# Migration from `mech-lab`

BLKBX Lab is the canonical public surface. The old `mechlab` CLI and `mech_lab` Python import remain as deprecated shims that delegate to `blkbx_lab`.

## Name Mapping

- Old package: `mechlab-sdk`
- New package: `blkbx-lab`
- Old CLI: `mechlab`
- New CLI: `blkbx-lab`
- Old Python import: `import mech_lab`
- New Python import: `import blkbx_lab`

## Artifact Mapping

- `mair_manifest.v1.json` -> `ink_manifest.v1.json`
- `assurance_receipt.v1.json` -> `ink_receipt.v1.json`
- `backend_comparison.v1.json` -> `receipt_comparison.v1.json`

## Migration Rule

- Use `blkbx-lab` and `blkbx_lab` in all new docs, examples, scripts, and release notes.
- Treat `mechlab` and `mech_lab` as temporary compatibility shims only.
