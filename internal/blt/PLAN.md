# BLT local checklist

Source of truth: [`../MAIR/PLAN.md`](../MAIR/PLAN.md)

## BLT-owned surfaces
- `src/blt/capture.py`
- `src/blt/export.py`
- `src/blt/integrations/posthoc.py`
- `src/blt/cli/run_trace.py`
- `configs/qwen3.5-2b.profile.json`

## Current operating notes
- keep `mock` backend for CI and fixture coverage
- keep the first real replay profile pinned to `Qwen/Qwen3.5-2B`
- require strict native `qwen3_5` preflight for real replay; fail closed on any `qwen3_next` drift
- on the validated `16 GiB` arm64/MPS host, `device:auto` was not robust enough for artifact emission and the successful public rerun used the documented CPU override profile

## Upstream dependency
- `MAIR` must be installed editable before BLT cross-repo tests and consumer integrations run
