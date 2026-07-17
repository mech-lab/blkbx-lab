import tomllib
import subprocess
from importlib.resources import files
from pathlib import Path

import blkbx_lab.artifacts as artifact_resources
from blkbx_lab._version import __version__
import blkbx_lab.evidence as evidence_resources


ROOT = Path(__file__).resolve().parents[1]


def test_root_package_uses_maturin_thin_waist_contract():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["build-system"]["build-backend"] == "maturin"
    assert data["project"]["name"] == "mechlab-sdk"
    assert data["project"]["version"] == __version__
    assert data["project"]["description"] == "Model-agnostic Ink Receipts with a no_std, no_alloc Rust trust waist"
    assert data["project"]["readme"] == {"file": "README.md", "content-type": "text/markdown"}
    assert sorted(data["project"]["dependencies"]) == ["cryptography>=42", "jsonschema>=4.23"]
    assert data["project"]["optional-dependencies"] == {
        "research": ["markdown-it-py>=3"],
        "experimental": ["rich>=13"],
        "all": ["markdown-it-py>=3", "rich>=13"],
        "dev": ["maturin>=1.7,<2", "pyright[nodejs]", "pytest", "ruff"],
    }
    assert data["project"]["scripts"] == {
        "blkbx-lab": "blkbx_lab.cli:main",
        "mechlab": "blkbx_lab.cli:main",
    }
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
    assert data["tool"]["pytest"]["ini_options"] == {
        "testpaths": ["tests"],
        "addopts": "-q --import-mode=importlib",
    }


def test_repo_uses_python_src_layout_without_root_package_shim():
    assert (ROOT / "python" / "blkbx_lab" / "__init__.py").exists()
    assert (ROOT / "python" / "mech_lab" / "__init__.py").exists()
    assert (ROOT / "python" / "blkbxs" / "__init__.py").exists()
    assert (ROOT / "python" / "mand8" / "__init__.py").exists()
    assert (ROOT / "python" / "due" / "__init__.py").exists()
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


def test_schema_resources_are_available_from_python_packages():
    evidence_schema = evidence_resources.load_schema("ink.evidence.record.v1")
    artifact_schema = artifact_resources.load_schema("ink.export_manifest.v1")

    assert evidence_schema["$id"].endswith("ink.evidence.record.v1.schema.json")
    assert artifact_schema["$id"].endswith("ink.export_manifest.v1.schema.json")
    assert files("blkbx_lab.schemas").joinpath("ink.evidence.record.v1.schema.json").is_file()
