# Tools

This directory holds local bootstrap helpers for MAIR and the BLT integration stack.

## Editable install bootstrap
Run:

```bash
./tools/bootstrap_editable.sh
```

This executes:

```bash
python -m pip install -e '/Volumes/128/MAIR[dev]' -e '/Volumes/128/BLT[dev]'
```

It installs the packages and their CLIs for local development without `PYTHONPATH` injections.
