import tomllib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_root_package_uses_maturin_thin_waist_contract():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["build-system"]["build-backend"] == "maturin"
    assert data["project"]["name"] == "blkbx-lab"
    assert data["project"]["version"] == "0.7.0"
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


def test_repo_uses_python_src_layout_without_root_package_shim():
    assert (ROOT / "python" / "blkbx_lab" / "__init__.py").exists()
    assert not (ROOT / "blkbx_lab").exists()
    assert not (ROOT / "adapters").exists()


def test_native_extension_is_not_tracked_in_git():
    tracked = subprocess.run(
        ["git", "ls-files", "python/blkbx_lab"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "_ink_native.abi3.so" not in tracked
