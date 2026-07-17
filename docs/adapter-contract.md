# Adapter Contract

This page describes the shipped public adapter behavior behind `blkbx-lab trace` and `blkbx_lab.trace()`.

## Installed Public Adapter

The current installed adapter registry exposes one public adapter:

- `qwen35`

The public teaching path is a bundled deterministic demo rather than a live provider integration.

## Compatibility Selectors

These selectors normalize to the shipped `qwen35` adapter:

- `qwen35`
- `qwen35-claims`
- `qwen3.5`
- `Qwen/Qwen3.5-2B`

## Trace Inputs

The public trace flow accepts:

- prompt text
- optional output directory
- optional trace id
- adapter selector within the supported compatibility set

Unsupported `adapter`, `family`, `model`, `backend`, or `profile` values fail loudly.

## Trace Outputs

The shipped deterministic demo writes:

- `prompt.txt`
- `action.json`
- `runtime.json`
- `demo_mapping.json`
- `model_waist.json`
- `ink_manifest.v2.json`

The follow-on receipt flow writes `ink_receipt.v2.json`.

## Documentation Boundary

Do not document additional runtimes, providers, or adapter protocols as supported public surface until they are registered in code and covered by the public-contract tests.
