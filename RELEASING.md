# Releasing `hybrid-mechlab` 0.1.0a1

This MVP release publishes only the base `hybrid-mechlab` package.

- `python-rust/` stays in-repo for internal development.
- `python-rust/` is not published in this MVP pass.
- The supported runtime path for the MVP release is `math_backend="python"`.

## Prerequisites

- Python 3.10 through 3.13
- Rust toolchain available for `cargo test` and fixture regeneration
- Python tooling installed:

```bash
python3 -m pip install build twine
```

## Pre-release checks

```bash
python3 -m pytest
cargo test
cargo run -q -p hm_examples --bin kernel_fixture > tests/fixtures/rust_kernel_fixture.json
python3 -m build
python3 -m twine check dist/*
```

## Wheel smoke test

```bash
tmpdir=$(mktemp -d)
python3 -m venv "$tmpdir/venv"
source "$tmpdir/venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install dist/*.whl
python - <<'PY'
from hybrid_mechlab import HybridLab, profiles
from hybrid_mechlab.topology.offline import compute_persistence

lab = HybridLab.attach(
    model="dummy-qwen",
    profile=profiles.reference.qwen35(),
    backend="adapter",
)
trace = lab.run(prompts=["Measure topology for a reference hybrid."])
print(trace.summary())
report = compute_persistence(trace)
print(report.summary.h0_pairs)
PY
```

Verify that:
- `import hybrid_mechlab` succeeds
- the README quickstart runs
- no Rust package is installed or required

## sdist smoke test

```bash
tmpdir=$(mktemp -d)
python3 -m venv "$tmpdir/venv"
source "$tmpdir/venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install dist/*.tar.gz
python - <<'PY'
from hybrid_mechlab import HybridLab, profiles
from hybrid_mechlab.topology.offline import compute_persistence

lab = HybridLab.attach(
    model="dummy-qwen",
    profile=profiles.reference.qwen35(),
    backend="adapter",
)
trace = lab.run(prompts=["Measure topology for a reference hybrid."])
print(trace.summary())
report = compute_persistence(trace)
print(report.summary.h0_pairs)
PY
```

Verify that:
- `import hybrid_mechlab` succeeds
- the README quickstart runs
- no Rust package is installed or required

## Publish

- Upload only the base package artifacts from `dist/`.
- Do not upload `python-rust/` artifacts in this MVP pass.
