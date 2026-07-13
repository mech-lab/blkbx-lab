# Contributing to BLKBX Lab

BLKBX Lab’s public contract is `blkbx-lab` / `blkbx_lab` plus Ink artifacts. New examples, docs, and tests should target that surface unless a change is explicitly about migration compatibility.

## Development Setup

1. Clone the repository.
2. Create a virtual environment: `python3 -m venv .venv`
3. Activate the environment: `source .venv/bin/activate`
4. Install in editable mode with dev dependencies: `pip install -e ".[dev]"`

## Testing

Run the targeted public-contract checks while editing docs, release metadata, or examples:

```bash
python -m pytest -q \
  tests/test_readme_example.py \
  tests/test_packaging_contracts.py \
  tests/test_release_readiness.py \
  tests/test_mech_lab_product.py \
  tests/test_mech_lab_doctor.py
```

Run the same verification matrix that CI uses when touching broader runtime code:

```bash
python -m pytest -q
python -m ruff check .
python -m pyright
```

## Code Style

We use `ruff` for linting and formatting, and `pyright` for type checking.

```bash
python -m ruff check .
python -m ruff format .
python -m pyright
```

## Documentation Rules

- Use `blkbx-lab` for the package and CLI.
- Use `blkbx_lab` for the Python namespace.
- Treat deprecated compatibility shims as migration-only surfaces.
- Use `ink_manifest.v1.json`, `ink_receipt.v1.json`, and `receipt_comparison.v1.json` when referring to public artifacts.
- Treat `hybrid_mechlab`, `internal/trace/legacy_blt`, `internal/ink/legacy_mair`, and placeholder research modules as experimental or historical surfaces, not the public BLKBX release contract.
