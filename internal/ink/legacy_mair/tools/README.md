# Tools

This directory holds local bootstrap helpers for MAIR and the BLT integration stack.

## Editable install bootstrap
Run:

```bash
./tools/bootstrap_editable.sh
```

This executes:

```bash
python -m pip install -e './internal/ink/legacy_mair[dev]' -e './internal/trace/legacy_blt[dev]'
```

It installs the packages and their CLIs for local development without `PYTHONPATH` injections.
