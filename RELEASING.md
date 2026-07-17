# Releasing `mechlab-sdk`

This repository publishes one public distribution: `mechlab-sdk`.

Primary release-facing surface:

- install package: `mechlab-sdk`
- primary CLI: `blkbx-lab`
- primary Python namespace: `blkbx_lab`
- stable product imports carried by the same wheel: `blkbxs`, `mand8`, `due`

Compatibility aliases are covered in the migration docs and compatibility smoke checks; they are not the primary documentation surface.

## Prerequisites

- Python `3.10+`
- Rust toolchain from [`rust-toolchain.toml`](rust-toolchain.toml)
- release workflow access for the `mech-lab/blkbx-lab` repository
- PyPI trusted publisher configured for project `mechlab-sdk`

## Pre-release Checks

Run the full release-readiness path from a clean checkout when preparing a candidate:

```bash
python3 scripts/check_release_readiness.py
python3 scripts/check_local_release.py
```

The release-readiness script validates:

- release-facing markdown terminology
- archived versus active docs boundaries
- authored release notes workflow usage
- host-ready social preview assets
- validation report appendix hygiene

## Local Release Candidate

For an in-progress local pass:

```bash
python3 scripts/check_release_readiness.py --skip-clean-worktree
python3 scripts/check_local_release.py \
  --skip-clean-worktree \
  --skip-build \
  --skip-smoke
```

## Build and Artifact Validation

The release script expects exactly one wheel and one sdist for the current version.

Manual equivalents:

```bash
python3 -m build
python3 -m twine check dist/*
```

## Fresh Install Smoke

The root wheel smoke path must prove:

- `blkbx_lab` imports from a fresh environment
- `blkbxs`, `mand8`, and `due` import from the same wheel
- `blkbx-lab demo` and `blkbx-lab doctor` work from a clean install

## Compatibility Smoke

Compatibility aliases remain shipped and should still be smoke-tested during release validation. Keep those checks in release automation and in the migration docs rather than in the primary quickstart material.

## Tag and Publish

1. Update versioned release notes using [`.github/RELEASE_TEMPLATE.md`](.github/RELEASE_TEMPLATE.md).
2. Push the release tag that triggers [`.github/workflows/release.yml`](.github/workflows/release.yml).
3. Confirm GitHub Release assets and PyPI artifacts match the tagged commit.

## Release-Facing Docs

Before publishing, confirm these sources still agree:

- [`README.md`](README.md)
- [`docs/README.md`](docs/README.md)
- [`docs/pypi.md`](docs/pypi.md)
- [`docs/release-readiness.md`](docs/release-readiness.md)
- [`docs/research/qwen35-validation-report.md`](docs/research/qwen35-validation-report.md)
- [`docs/brand/release-copy.md`](docs/brand/release-copy.md)
