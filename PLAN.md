# BLT local checklist

Source of truth: [`../MAIR/PLAN.md`](../MAIR/PLAN.md)

## BLT-owned surfaces
- `src/blt/capture.py`
- `src/blt/export.py`
- `src/blt/integrations/posthoc.py`
- `src/blt/cli/run_trace.py`
- `configs/qwen3.5-2b.profile.json`

## Current blockers
- remove MAIR path fallback and rely on editable installs
- keep `mock` backend for CI while moving the live flow to `qwen_hybrid_hf`
- pin and test the first real replay profile against `Qwen/Qwen3.5-2B`

## Upstream dependency
- `MAIR` must be installed editable before BLT cross-repo tests and consumer integrations run
