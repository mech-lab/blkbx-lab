# Releasing `blkbx-lab`

This repo publishes one public distribution: `blkbx-lab`.

Release-facing contract:

- repository and product name: `blkbx-lab`
- published package name: `blkbx-lab`
- CLI name: `blkbx-lab`
- Python import path: `blkbx_lab`

In-repo but not first-class public release surfaces:

- `hybrid_mechlab`
- `internal/trace/legacy_blt`
- `internal/ink/legacy_mair`
- `legacy/hybrid-mechlab-python`
- `legacy/python-rust`
- deprecated compatibility shims

Brand release kit:

- GitHub repo and release notes use [`.github/RELEASE_TEMPLATE.md`](.github/RELEASE_TEMPLATE.md)
- PyPI long description is sourced from [`docs/pypi.md`](docs/pypi.md)
- launch assets live under [`assets/brand/`](assets/brand)
- brand tokens and copy rules live under [`docs/brand/`](docs/brand)
- `assets/brand/og-card.png` is the live GitHub social preview export

PyPI publish path:

- tagged releases publish to PyPI from [`.github/workflows/release.yml`](.github/workflows/release.yml)
- the same workflow can also publish manually through `workflow_dispatch`
- the publish job uses GitHub trusted publishing through the `pypi` environment

Release readiness gate:

- the git worktree must be clean before any public tag
- `python scripts/check_release_readiness.py` is the repo-native readiness check
- [`docs/release-readiness.md`](docs/release-readiness.md) is the operator checklist for the final documentation and repo-ergonomics pass

## Prerequisites

- Python 3.10 through 3.13
- Rust toolchain available for the legacy companion package checks
- Python tooling installed:

```bash
python3 -m pip install build twine pytest
```

## First-Time PyPI Setup

Before the first public PyPI publish, create a pending trusted publisher for project `blkbx-lab` on PyPI with these values:

- project name: `blkbx-lab`
- GitHub owner: `mech-lab`
- GitHub repository: `blkbx-lab`
- workflow file: `release.yml`
- environment name: `pypi`

Repo-side requirements:

- the GitHub environment `pypi` must exist on the `mech-lab/blkbx-lab` repository
- [`.github/workflows/release.yml`](.github/workflows/release.yml) must stay on the default branch
- the first publish should run from a release tag such as `v0.1.0a2`

## Pre-release checks

```bash
python scripts/check_release_readiness.py
python3 -m pytest \
  tests/test_brand_release_assets.py \
  tests/test_packaging_contracts.py \
  tests/test_readme_example.py \
  tests/test_release_readiness.py \
  tests/test_mech_lab_product.py \
  tests/test_mech_lab_doctor.py \
  tests/test_version_sync.py
python3 -m build
python3 -m twine check dist/*
```

Verify that:

- `python scripts/check_release_readiness.py` passes on a clean tree
- the root build emits only `blkbx-lab` distribution artifacts
- the README quickstart examples still run from a fresh environment
- the deprecated shims still delegate and warn
- the brand asset tests pass
- the GitHub social preview PNG export is present at `assets/brand/og-card.png`
- the Qwen validation report keeps workstation-specific paths inside its reproducibility appendix only

## Wheel smoke test

```bash
tmpdir=$(mktemp -d)
python3 -m venv "$tmpdir/venv"
source "$tmpdir/venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install dist/*.whl
python - <<'PY'
import blkbx_lab as bl

result = bl.demo(output_dir="artifacts/release-wheel")
print(result.manifest_path)
print(result.receipt_path)
print(bl.verify(result.receipt_path).report)
PY
blkbx-lab doctor >/dev/null
```

Verify that:

- `import blkbx_lab` succeeds
- the `blkbx-lab` CLI is installed
- the public quickstart works without installing any separate legacy companion package

## sdist smoke test

```bash
tmpdir=$(mktemp -d)
python3 -m venv "$tmpdir/venv"
source "$tmpdir/venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install dist/*.tar.gz
python - <<'PY'
import blkbx_lab as bl

result = bl.demo(output_dir="artifacts/release-sdist")
print(result.manifest_path)
print(result.receipt_path)
print(bl.verify(result.receipt_path).report)
PY
```

Verify that:

- `import blkbx_lab` succeeds
- the public quickstart works from the source distribution
- the deprecated compatibility shim path is not the documented release path

## Tag and publish

- Tag releases as the package version, for example `v0.1.0a2`.
- GitHub Releases should mirror the PyPI release notes for `blkbx-lab`.
- The release workflow creates a draft release from `.github/RELEASE_TEMPLATE.md`; edit the draft body before publishing it.
- Tagged releases publish `dist/*` to PyPI through the `pypi` environment, and `workflow_dispatch` can publish the same distributions manually when needed.
- Upload only the root `dist/` artifacts.
- Attach the branded launch assets from `assets/brand/og-card.svg`, `assets/brand/og-card.png`, `assets/brand/launch-card.svg`, and `assets/brand/release-header.svg`.

## Live GitHub checks

Before publishing the draft release, verify the live host state:

- the GitHub repository metadata matches `.github/settings.yml`
- the README renders correctly on GitHub
- the release draft includes the branded asset attachments and a readable body
- the repository social preview uses `assets/brand/og-card.png`
- the social preview and attached SVG assets remain legible in GitHub light and dark themes
- the PyPI trusted publisher matches `blkbx-lab / mech-lab / blkbx-lab / release.yml / pypi`
