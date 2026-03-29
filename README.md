# MAIR

MAIR is the canonical artifact contract for the BLT v1 stack.

It owns:
- typed artifact names and stable filenames
- deterministic IDs and content hashes
- manifest generation and validation
- the tracked cross-repo implementation plan

## Editable install
The supported local development path is:

```bash
python -m pip install -e '/Volumes/128/MAIR[dev]' -e '/Volumes/128/BLT[dev]'
```

That makes these CLIs available without `PYTHONPATH` hacks:
- `mair-validate`
- `mair-write-manifest`
- `blt-run-trace`
- `blt-fit-grouped-clt`
- `blt-run-analysis`

For the real Qwen replay backend, also install the BLT model extra or equivalent runtime deps:

```bash
python -m pip install -e '/Volumes/128/BLT[model]'
```

## Tools
- `tools/bootstrap_editable.sh`: installs MAIR and BLT editable for local cross-repo development

## Plan
- Source of truth: [`PLAN.md`](PLAN.md)
