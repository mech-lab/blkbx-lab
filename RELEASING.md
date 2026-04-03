# Releasing `mech-lab`

This repo publishes one public distribution: `mech-lab`.

Release-facing contract:

- repository and package name: `mech-lab`
- CLI name: `mechlab`
- Python import path: `mech_lab`

In-repo but not published as first-class public releases:

- `internal/blt`
- `internal/mair`
- `legacy/hybrid-mechlab-python`
- `legacy/python-rust`

Internal BLT and MAIR changes ship inside the `mech-lab` release notes rather than as separate public releases.

Brand release kit:

- GitHub repo and release notes use [`.github/RELEASE_TEMPLATE.md`](.github/RELEASE_TEMPLATE.md)
- PyPI long description is sourced from [`docs/pypi.md`](docs/pypi.md)
- launch assets live under [`assets/brand/`](assets/brand)
- brand tokens and usage rules live under [`docs/brand/`](docs/brand)
- `assets/brand/og-card.png` is the live GitHub social preview export; the SVG assets remain the design source of truth

PyPI publish path:

- tagged releases publish to PyPI from [`.github/workflows/release.yml`](.github/workflows/release.yml)
- the same workflow can also publish manually through `workflow_dispatch`
- the publish job uses GitHub trusted publishing through the `pypi` environment
- `pip install mech-lab` will not resolve until the PyPI-side trusted publisher is configured

Release readiness gate:

- the git worktree must be clean before any public tag
- `python scripts/check_release_readiness.py` is the repo-native readiness check
- [`docs/release-readiness.md`](docs/release-readiness.md) is the operator checklist for the final documentation and repo-ergonomics pass

## Prerequisites

- Python 3.10 through 3.13
- Rust toolchain available for `cargo test` and fixture regeneration
- Python tooling installed:

```bash
python3 -m pip install build twine pytest
```

## First-Time PyPI Setup

Before the first public PyPI publish, create a pending trusted publisher for project `mech-lab` on PyPI with these values:

- project name: `mech-lab`
- GitHub owner: `mech-lab`
- GitHub repository: `mech-lab`
- workflow file: `release.yml`
- environment name: `pypi`

Repo-side requirements:

- the GitHub environment `pypi` must exist on the `mech-lab/mech-lab` repository
- [`.github/workflows/release.yml`](.github/workflows/release.yml) must stay on the default branch
- the first publish should run from a release tag such as `v0.1.0a1`

Once the PyPI pending publisher is approved, either rerun the `Release` workflow manually from `main` to publish the current version or push the next release tag.

## Pre-release checks

```bash
python scripts/check_release_readiness.py
python3 -m pytest \
  tests/test_release_readiness.py \
  tests/test_brand_release_assets.py \
  tests/test_packaging_contracts.py \
  tests/test_readme_example.py \
  tests/test_mech_lab_doctor.py \
  tests/test_mech_lab_product.py \
  tests/test_mair_import.py \
  tests/test_version_sync.py
python3 -m pytest internal/blt/tests/test_trace.py internal/mair/tests/test_manifest.py
cargo test
cargo run -q -p hm_examples --bin kernel_fixture > tests/fixtures/rust_kernel_fixture.json
python3 -m build
python3 -m twine check dist/*
```

Verify that:

- `python scripts/check_release_readiness.py` passes on a clean tree
- the root build emits only `mech-lab` artifacts
- the README quickstart examples still run from a fresh environment
- internal BLT and MAIR tests still pass inside the unified repo
- the brand asset tests pass
- the launch SVG assets are present and ready to attach to the GitHub release
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
import mech_lab as ml

bundle = ml.demo(output_dir="artifacts/release-wheel")
print(bundle.manifest_path)
print(ml.report(bundle))
PY
mechlab doctor >/dev/null
```

Verify that:

- `import mech_lab` succeeds
- the `mechlab` CLI is installed
- the README quickstart works without installing any separate BLT or MAIR package

## sdist smoke test

```bash
tmpdir=$(mktemp -d)
python3 -m venv "$tmpdir/venv"
source "$tmpdir/venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install dist/*.tar.gz
python - <<'PY'
import mech_lab as ml

bundle = ml.demo(output_dir="artifacts/release-sdist")
print(bundle.manifest_path)
print(ml.report(bundle))
PY
```

Verify that:

- `import mech_lab` succeeds
- the public quickstart works from the source distribution
- nothing under `internal/` or `legacy/` is published as a separate package

## Tag and publish

- Tag releases as the package version, for example `v0.1.0a1`.
- GitHub Releases should mirror the PyPI release notes for `mech-lab`.
- The release workflow creates a draft release from `.github/RELEASE_TEMPLATE.md`; edit the draft body before publishing it.
- Tagged releases publish `dist/*` to PyPI through the `pypi` environment, and `workflow_dispatch` can publish the same distributions manually when needed.
- Upload only the root `dist/` artifacts.
- Attach the branded launch assets from `assets/brand/og-card.svg`, `assets/brand/og-card.png`, `assets/brand/launch-card.svg`, and `assets/brand/release-header.svg`.
- Do not publish anything from `internal/` or `legacy/`.

## Live GitHub checks

Before publishing the draft release, verify the live host state:

- the GitHub repository metadata matches `.github/settings.yml`
- the README renders correctly on GitHub
- the release draft includes the branded asset attachments and a readable body
- the repository social preview uses `assets/brand/og-card.png`
- the social preview and attached SVG assets remain legible in GitHub light and dark themes
- the PyPI trusted publisher matches `mech-lab / mech-lab / release.yml / pypi`
