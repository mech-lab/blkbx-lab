# BLT

BLT materializes hybrid block traces into MAIR artifacts.

It provides:
- a real `qwen_hybrid_hf` replay backend for the pinned `Qwen/Qwen3.5-2B` profile
- deterministic mock Qwen3.5-style hybrid traces for CI-safe fixture coverage
- BLT artifact writers for MAIR
- grouped CLT bundle generation
- topology sketch summaries

## Editable install
The supported local development path is:

```bash
python -m pip install -e '/Volumes/128/MAIR[dev]' -e '/Volumes/128/BLT[dev]'
```

For the real replay backend, also install:

```bash
python -m pip install -e '/Volumes/128/BLT[model]'
```

## Built-in profile
- `configs/qwen3.5-2b.profile.json`: pinned first real hybrid replay target

## Backend modes
- `mock`: deterministic fixture backend for CI and explicit local smoke runs
- `qwen_hybrid_hf`: real Hugging Face replay backend for the pinned Qwen profile

CLI:
- `blt-run-trace`
- `blt-fit-grouped-clt`
- `blt-run-analysis`
