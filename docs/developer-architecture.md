# Developer Architecture

BLKBX Lab is structured into the following layers:

```text
blkbx-lab CLI / blkbx_lab SDK
        |
        +-- internal/trace   model event capture, action proposal capture
        |
        +-- internal/ink     manifest, canonicalization, signing, verification
        |
        +-- internal/gates   gate policies, decisions, receipt issuance
        |
        +-- adapters/        qwen35, vllm, sglang, openai-compatible
```

## Public Facade (`blkbx_lab/`)

The public SDK and CLI. This is the only layer users should interact with directly.

## Internal Trace Layer (`internal/trace/`)

Responsible for capturing model events and action proposals.

## Internal Ink Layer (`internal/ink/`)

Handles the core Ink Receipt logic: manifests, canonicalization, signing, and verification.

## Internal Gates Layer (`internal/gates/`)

Evaluates actions against policies and makes decisions (pass, warn, escalate, block).

## Adapters (`adapters/`)

Provides a thin-waist interface to different models and runtimes.
