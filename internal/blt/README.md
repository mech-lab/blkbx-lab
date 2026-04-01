# BLT

BLT is the bundled internal trace-capture subsystem for `mech-lab`.

It provides:

- the real `qwen_hybrid_hf` replay backend for the pinned `Qwen/Qwen3.5-2B` profile
- deterministic mock Qwen3.5-style hybrid traces for CI-safe coverage
- export from trace capture into MAIR-native artifacts
- grouped CLT bundle generation and topology summaries

## Unified repo development

From the repo root:

```bash
python -m pip install -e './internal/mair[dev]' -e './internal/blt[dev]'
```

For the real replay backend, also install:

```bash
python -m pip install -e './internal/blt[model]'
```

`qwen_hybrid_hf` requires a native `qwen3_5` runtime, not a structural surrogate. BLT performs a strict preflight against the real `Qwen/Qwen3.5-2B` checkpoint before tokenizer or model load and requires:

- `AutoConfig.from_pretrained("Qwen/Qwen3.5-2B")`
- `model_type == "qwen3_5"`
- auto-factory resolution to `transformers.models.qwen3_5.modeling_qwen3_5.Qwen3_5ForConditionalGeneration`

Anything that would drift to `qwen3_next` fails closed before replay.

Validated runtime note:

- the canonical public rerun evidence is recorded in [../../docs/qwen35-validation-report.md](../../docs/qwen35-validation-report.md)
- on the validated `16 GiB` arm64/MPS host, the successful public rerun used the documented CPU override after `device:auto` failed before artifact emission

## Internal status

- This is an internal subsystem, not a separate public release target.
- Generated caches and build outputs are disposable.
- The tracked `src/*.egg-info` policy remains deferred.

## Built-in profile

- `configs/qwen3.5-2b.profile.json`: pinned first real hybrid replay target

## Backend modes

- `mock`: deterministic fixture backend for CI and explicit local smoke runs
- `qwen_hybrid_hf`: real Hugging Face replay backend for the pinned Qwen profile
