# Qwen3.5 Validation Report

## Scope

This document records the native `Qwen/Qwen3.5-2B` validation state of the public `mechlab` Qwen3.5 product lane on April 1, 2026.

Canonical product command:

```bash
mechlab trace --family qwen3.5 --model qwen3.5-2b --prompt "Measure the 3:1 tract bridge rhythm."
```

## Runtime evidence

Canonical native runtime root:
- `/Volumes/2.5SSDDD128/mechlab-qwen35-native`

Environment summary:
- Python: `3.12.11`
- torch: `2.11.0`
- transformers: `5.5.0.dev0`
- transformers source: `/Volumes/2.5SSDDD128/mechlab-qwen35-native/src/transformers-upstream`
- transformers commit: `9914a3641f7aaaabb0bcdfcd73a54a1cfa70c3e7`
- cached model snapshot: `15852e8c16360a2fea060d615a32b45270f8a8fc`
- cached weight artifact: `model.safetensors-00001-of-00001.safetensors`

Workspace-local cache and temp roots used for the rerun:
- `TMPDIR=/Volumes/2.5SSDDD128/mechlab-qwen35-native/tmp`
- `HF_HOME=/Volumes/2.5SSDDD128/mechlab-qwen35-native/hf-home`
- `HUGGINGFACE_HUB_CACHE=/Volumes/2.5SSDDD128/mechlab-qwen35-native/hf-cache`
- `TRANSFORMERS_CACHE=/Volumes/2.5SSDDD128/mechlab-qwen35-native/transformers-cache`
- `PIP_CACHE_DIR=/Volumes/2.5SSDDD128/mechlab-qwen35-native/pip-cache`

Native preflight proof:
- `mechlab doctor` reports native Qwen readiness
- the runtime resolves:
  - config class: `transformers.models.qwen3_5.configuration_qwen3_5.Qwen3_5Config`
  - model class: `transformers.models.qwen3_5.modeling_qwen3_5.Qwen3_5ForConditionalGeneration`
- `qwen3_next` was evaluated only as a structural debugging reference and was not used in the shipped runtime path or the validation rerun

## Public rerun result

`mechlab doctor` succeeded with native `qwen3_5` detection:
- status: `ready`
- `transformers` check: native config and model classes resolved through the real checkpoint

First public real-model attempt:
- command: builtin BLT profile with `device:auto`
- result: weights loaded successfully, but the process exited before emitting any MAIR artifacts
- host note: this machine is `arm64` with `16 GiB` RAM, and BLT `device:auto` resolves to `mps` on this host
- recorded evidence: `/Volumes/2.5SSDDD128/mechlab-qwen35-native/artifacts/qwen35-real-run-auto.log`

Successful public rerun:
- command:

```bash
mechlab trace \
  --family qwen3.5 \
  --model qwen3.5-2b \
  --profile /Volumes/2.5SSDDD128/mechlab-qwen35-native/artifacts/qwen35-cpu.profile.json \
  --prompt "Measure the 3:1 tract bridge rhythm." \
  --output-dir /Volumes/2.5SSDDD128/mechlab-qwen35-native/artifacts/qwen35-real-run
```

- result: success through the public `mechlab` façade only
- manifest: `/Volumes/2.5SSDDD128/mechlab-qwen35-native/artifacts/qwen35-real-run/mair_manifest.v1.json`
- receipt: `/Volumes/2.5SSDDD128/mechlab-qwen35-native/artifacts/qwen35-real-run/assurance_receipt.v1.json`

Public follow-up commands that succeeded:

```bash
mechlab analyze /Volumes/2.5SSDDD128/mechlab-qwen35-native/artifacts/qwen35-real-run/mair_manifest.v1.json --profile qwen3.5-hybrid --output-dir /Volumes/2.5SSDDD128/mechlab-qwen35-native/artifacts/qwen35-real-run
mechlab report /Volumes/2.5SSDDD128/mechlab-qwen35-native/artifacts/qwen35-real-run/mair_manifest.v1.json --kind tract-vs-bridge
mechlab gate /Volumes/2.5SSDDD128/mechlab-qwen35-native/artifacts/qwen35-real-run/mair_manifest.v1.json --policy release-assurance
```

Analyzed artifacts present in the MAIR-native bundle:
- `mair_semantic_trace.v1.jsonl`
- `mair_graph_ir.v1.json`
- `mair_numeric_lowering.v1.json`
- `blt_codes.v1.parquet`
- `tract_state_snapshot.v1.parquet`
- `topology_summary.v1.json`
- `grouped_clt_bundle.v1.json`
- `offline_topology_report.v1.json`
- `intervention_sweep.v1.jsonl`
- `assurance_receipt.v1.json`

Required hook coverage validated from the real run:
- `pre-D1`
- `post-D1`
- `post-D2`
- `post-D3`
- `post-attention`
- `block-output`

Real-run analysis summary:
- trace id: `trace-mechlab-20260401-081029`
- tract retention: `0.953495`
- topology bridge dependence: `0.25`
- grouped bridge dependence: `0.078713`
- mean reconstruction divergence: `0.046505`
- gate decision: `pass`

Report render proof:
- `mechlab report ... --kind tract-vs-bridge` rendered successfully from the MAIR manifest with no BLT-internal command usage

## Exit artifact status

- public entrypoint implemented: yes
- family/model flag mapping implemented: yes
- native `qwen3_5` runtime verified against the real checkpoint: yes
- weight fetch completed into workspace storage: yes
- real-model replay completed successfully on this machine: yes
- successful rerun path used surrogate runtime aliases: no
- successful rerun path used public `mechlab` façade only: yes
- successful rerun path required CPU override profile after `device:auto` failed on this host: yes
