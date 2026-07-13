# BLT + MAIR v1 Master Plan

This is the tracked source-of-truth plan for the BLT + MAIR v1 implementation.

## Current state
- `MAIR` owns schemas, deterministic IDs, manifests, and validation.
- `BLT` owns trace capture, BLT artifact generation, grouped CLT analysis, and topology sketches.
- `posthoc` owns trace lifecycle and artifact retrieval by `trace_id`.
- `hypercircuit` consumes BLT outputs for staged analysis.
- `Geo-CLT-SAE` consumes MAIR manifests for gates and receipts.
- `featurecircuit-protocol` consumes MAIR manifests for HIF compatibility exports.

## Repo ownership
- `MAIR`: contract repo and master plan home
- `BLT`: hybrid capture backend and artifact generation
- `posthoc`: async artifact materialization and retrieval
- `hypercircuit`: downstream grouped-CLT reporting
- `Geo-CLT-SAE`: assurance and receipt evaluation
- `featurecircuit-protocol`: MAIR-to-HIF bridge

## Local development bootstrap
Supported command from the unified repo root:

```bash
python -m pip install -e './internal/ink/legacy_mair[dev]' -e './internal/trace/legacy_blt[dev]'
```

Real Qwen replay additionally requires BLT model dependencies.

## Commit order
1. `MAIR`: `mair: track master plan and editable-install contract`
2. `BLT`: `blt: add backend abstraction and pinned qwen replay profile`
3. `posthoc`: `sidecar: use BLT replay backend for async artifact materialization`
4. `hypercircuit`: `hypercircuit: consume installed BLT and MAIR packages`
5. `Geo-CLT-SAE`: `geoclt: benchmark installed MAIR manifests without path hacks`
6. `featurecircuit-protocol`: `featurecircuit: bridge installed MAIR manifests to HIF`

## Real-hook cutover checklist
- [ ] Keep `mock` backend for CI and fixture coverage only.
- [x] Add `qwen_hybrid_hf` backend in BLT.
- [x] Pin the first real profile to `Qwen/Qwen3.5-2B`.
- [ ] Wire `posthoc` to use `BLT_CAPTURE_BACKEND` and `BLT_MODEL_PROFILE`.
- [ ] Remove absolute `/Volumes/.../src` import fallbacks from production modules.
- [ ] Remove absolute cross-repo `sys.path` patching from consumer tests.
- [ ] Install MAIR and BLT editable before cross-repo test runs.

## Acceptance criteria for retiring the live mock path
The mock backend remains available, but it is no longer the live `posthoc` path once all are true:
- `posthoc` materializes BLT artifacts through the real replay backend under the same `trace_id`.
- The real backend writes the full MAIR/BLT artifact set without falling back to `mock`.
- `hypercircuit`, `Geo-CLT-SAE`, and `featurecircuit-protocol` run against installed packages only.
- [x] A manual smoke run against `Qwen/Qwen3.5-2B` completes end to end and emits an assurance receipt.

## Qwen3.5 milestone status
- Native `qwen3_5` runtime proof is complete through the public `blkbx-lab` facade.
- The validated runtime evidence, manifest path, and receipt path are recorded in `../../docs/research/qwen35-validation-report.md`.
- On the validated `16 GiB` arm64/MPS host, `device:auto` required a documented CPU override fallback for the successful public rerun.
- Remaining follow-up is a CLI semantics issue in `mechlab gate --profile`, not a runtime blocker.
