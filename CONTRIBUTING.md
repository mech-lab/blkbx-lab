# Contributing to BLKBX Lab

Thank you for your interest in contributing to BLKBX Lab!

## Development Setup

1. Clone the repository.
2. Create a virtual environment: `python3 -m venv .venv`
3. Activate the environment: `source .venv/bin/activate`
4. Install in editable mode with dev dependencies: `pip install -e ".[dev]"`

## Testing

Run the test suite using `pytest`:

```bash
pytest
```

## Code Style

We use `ruff` for linting and formatting, and `pyright` for type checking.

```bash
ruff check .
ruff format .
pyright
```
