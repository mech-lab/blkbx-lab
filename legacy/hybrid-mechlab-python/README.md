# hybrid-mechlab-python

Minimal Python-only split of `hybrid-mechlab`.

This repo keeps the NumPy-backed trace, schedule, kernel, and offline topology
surfaces while dropping the Rust workspace, BLT sidecar, adapters, hooks, and
visualization modules.

## Install

```bash
pip install .
```

- The package depends only on `numpy`.
- `math_backend="python"` is the only supported backend in this repo.
- The import package remains `hybrid_mechlab`.

## Quickstart

```python
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
```

## Included Surface

- `HybridLab`
- `profiles`
- `hybrid_mechlab.kernel`
- `hybrid_mechlab.topology.offline`
- `hybrid_mechlab.experiments.long_context`

## Validation

```bash
python3 -m pytest
python3 -m build
```
