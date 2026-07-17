from __future__ import annotations

from pathlib import Path

import tomllib


ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_uses_maturin_and_canonical_python_package() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["build-system"]["build-backend"] == "maturin"
    assert data["tool"]["maturin"]["manifest-path"] == "rust/crates/ink-py/Cargo.toml"
    assert data["tool"]["maturin"]["python-source"] == "python"
    assert data["tool"]["maturin"]["python-packages"] == [
        "blkbx_lab",
        "blkbx_lab/adapters",
        "blkbx_lab/artifacts",
        "blkbx_lab/evidence",
        "blkbx_lab/experimental",
        "blkbx_lab/policies",
        "blkbx_lab/products",
        "blkbx_lab/products/blkbxs",
        "blkbx_lab/products/due",
        "blkbx_lab/products/mand8",
        "blkbx_lab/research",
        "blkbx_lab/schemas",
        "mech_lab",
        "blkbxs",
        "mand8",
        "mand8/bundles",
        "mand8/schemas",
        "due",
        "due/bundles",
        "due/schemas",
    ]
    assert data["tool"]["maturin"]["module-name"] == "blkbx_lab._ink_native"
