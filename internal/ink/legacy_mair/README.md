# MAIR

MAIR is the bundled historical artifact-contract subsystem preserved inside `blkbx-lab`.

It owns:

- typed artifact names and stable filenames
- deterministic IDs and content hashes
- manifest generation and hydration
- artifact validation and gating

## Unified repo development

From the repo root:

```bash
python -m pip install -e './internal/ink/legacy_mair[dev]' -e './internal/trace/legacy_blt[dev]'
```

That makes these CLIs available for local development:

- `mair-validate`
- `mair-write-manifest`
- `blt-run-trace`
- `blt-fit-grouped-clt`
- `blt-run-analysis`

For the real Qwen replay backend, also install the BLT model extra:

```bash
python -m pip install -e './internal/trace/legacy_blt[model]'
```

## Tools

- `tools/bootstrap_editable.sh`: installs the bundled internal MAIR and BLT packages from the unified repo

## Internal status

- This is an internal subsystem, not a separate public release target.
- Generated caches and local build outputs are disposable.
- The tracked `src/*.egg-info` policy remains deferred.

## Plan

- Source of truth: [`PLAN.md`](PLAN.md)
