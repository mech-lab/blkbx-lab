from __future__ import annotations

from pathlib import Path

import tomllib


ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_uses_maturin_and_canonical_python_package() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["build-system"]["build-backend"] == "maturin"
    assert data["tool"]["maturin"]["manifest-path"] == "rust/crates/ink-py/Cargo.toml"
    assert data["tool"]["maturin"]["python-source"] == "python"
    assert data["tool"]["maturin"]["python-packages"] == ["blkbx_lab"]
    assert data["tool"]["maturin"]["module-name"] == "blkbx_lab._ink_native"
