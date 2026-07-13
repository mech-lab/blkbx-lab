# BLKBX Lab TODO

Repository: `https://github.com/mech-lab/blkbx-lab.git`

## Public Contract

- [ ] Keep `blkbx-lab` / `blkbx_lab` as the only canonical package, CLI, and namespace in new docs and examples.
- [ ] Retire the deprecated compatibility shims once downstream migration no longer requires them.
- [ ] Keep public artifact names fixed at `ink_manifest.v1.json`, `ink_receipt.v1.json`, and `receipt_comparison.v1.json`.

## Product Hardening

- [ ] Replace the built-in demo signing key with configurable production signing support.
- [ ] Add richer canonical report views without expanding the public artifact schema.
- [ ] Keep the public adapter surface limited to registered names plus shipped Qwen aliases unless the product scope expands.

## Demo And Verification

- [ ] Keep `blkbx-lab demo qwen35-claims` as a deterministic teaching path.
- [ ] Add more explicit CLI output around the blocked gate decision and human-review requirement.
- [ ] Add richer verification examples for the Python API.

## Release Discipline

- [ ] Keep release-facing docs, templates, and workflow smoke tests aligned with the BLKBX contract.
- [ ] Keep `docs/research/qwen35-validation-report.md` current with the public surface that actually ships.
- [ ] Continue scoping old names to migration-only material.

## Research And History

- [ ] Preserve the `hybrid_mechlab`, `legacy_blt`, and `legacy_mair` trees as historical or research context without promoting them to the public release surface.
- [ ] Keep placeholder research modules explicitly marked experimental and out of the canonical BLKBX docs and smoke paths.
- [ ] Decide whether any research-only content should move to a separate package or archive.
