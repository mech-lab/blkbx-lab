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

## Prerequisites

- Python 3.10 through 3.13
- Rust toolchain available for `cargo test` and fixture regeneration
- Python tooling installed:

```bash
python3 -m pip install build twine pytest
```

## Pre-release checks

```bash
python3 -m pytest \
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

- the root build emits only `mech-lab` artifacts
- the README quickstart examples still run from a fresh environment
- internal BLT and MAIR tests still pass inside the unified repo

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
- Upload only the root `dist/` artifacts.
- Do not publish anything from `internal/` or `legacy/`.
