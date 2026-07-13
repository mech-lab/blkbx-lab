import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_root_package_uses_maturin_thin_waist_contract():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["build-system"]["build-backend"] == "maturin"
    assert data["project"]["name"] == "blkbx-lab"
    assert data["project"]["version"] == "0.6.0"
    assert data["project"]["description"] == "Model-agnostic Ink Receipts with a no_std, no_alloc Rust trust waist"
    assert data["project"]["readme"] == {"file": "README.md", "content-type": "text/markdown"}
    assert sorted(data["project"]["dependencies"]) == ["cryptography>=42", "jsonschema>=4.23"]
    assert data["project"]["scripts"] == {"blkbx-lab": "blkbx_lab.cli:main"}
    assert data["tool"]["maturin"]["manifest-path"] == "rust/crates/ink-py/Cargo.toml"
    assert data["tool"]["maturin"]["module-name"] == "blkbx_lab._ink_native"
    assert data["tool"]["pytest"]["ini_options"] == {
        "testpaths": ["tests"],
        "addopts": "-q --import-mode=importlib",
    }


def test_legacy_rust_package_remains_quarantined_under_legacy_namespace():
    data = tomllib.loads((ROOT / "legacy" / "python-rust" / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["name"] == "hybrid-mechlab-rust"
    assert data["build-system"]["build-backend"] == "maturin"
    assert data["tool"]["maturin"]["manifest-path"] == "../../rust/hm_pyo3/Cargo.toml"
