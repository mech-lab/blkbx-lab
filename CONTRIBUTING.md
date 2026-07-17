# Contributing to BLKBX Lab

BLKBX Lab’s shipped documentation contract is:

- install package: `mechlab-sdk`
- primary CLI docs surface: `blkbx-lab`
- primary Python docs surface: `blkbx_lab`
- public artifacts: `ink_manifest.v2.json`, `ink_receipt.v2.json`, `receipt_comparison.v2.json`

Start from the [docs hub](docs/README.md) when changing public-facing material.

## Development Setup

1. Clone the repository.
2. Create a virtual environment: `python3 -m venv .venv`
3. Activate it: `source .venv/bin/activate`
4. Install editable dev dependencies: `pip install -e ".[dev]"`

## Testing

Run the focused public-contract checks when editing docs, release metadata, examples, or packaging-facing copy:

```bash
python3 -m pytest -q \
  tests/test_readme_example.py \
  tests/test_packaging_contracts.py \
  tests/test_release_readiness.py \
  tests/test_mech_lab_product.py \
  tests/test_mech_lab_doctor.py
```

Run the broader verification matrix when touching runtime or packaging code:

```bash
python3 -m pytest -q
python3 -m ruff check .
python3 -m pyright
```

## Documentation Rules

- Use `mechlab-sdk` for install and published-package language.
- Use `blkbx-lab` for primary CLI narration and examples.
- Use `blkbx_lab` for the primary Python surface.
- Keep compatibility aliases inside migration or compatibility sections only.
- Use only shipped CLI verbs: `demo`, `doctor`, `trace`, `analyze`, `gate`, `verify`, `compare`, `tamper`, `explain`, `report`.
- Use only `ink_manifest.v2.json`, `ink_receipt.v2.json`, and `receipt_comparison.v2.json` in active docs.
- Treat `docs/archive/` as historical material, not onboarding or release-facing source of truth.

## Code Style

- Run `python3 -m ruff check .` before finalizing Python changes.
- Keep public examples executable when possible, especially the first Python block in [`README.md`](README.md).
- Update release-facing docs and release checks together when the public contract changes.
