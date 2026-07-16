# Migration from `mech-lab`

Black Box Labs is the product brand. `mechlab-sdk` is the current carrier package on PyPI, and the compatibility names remain active instead of retired.

## Name Mapping

- Published package: `mechlab-sdk`
- CLIs: `mechlab`, `blkbx-lab`
- Runtime namespaces: `import mech_lab`, `import blkbx_lab`
- Stable product imports from the same install: `import blkbxs`, `import mand8`, `import due`

## Artifact Mapping

- `mair_manifest.v1.json` -> `ink_manifest.v1.json`
- `assurance_receipt.v1.json` -> `ink_receipt.v1.json`
- `backend_comparison.v1.json` -> `receipt_comparison.v1.json`

## Migration Rule

- Use `mechlab-sdk` for installation instructions.
- Use `blkbx-lab` or `mechlab` for CLI examples when you want to show both installed entry points.
- Use `blkbx_lab` for shared runtime examples and `blkbxs`, `mand8`, or `due` for market-specific Python examples.
