import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_root_package_uses_blkbx_release_metadata():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["build-system"]["build-backend"] == "setuptools.build_meta"
    assert data["project"]["name"] == "blkbx-lab"
    assert data["project"]["version"] == "0.1.0a2"
    assert data["project"]["description"] == "Open-source Ink Receipt gates for accountable AI agents"
    assert data["project"]["readme"] == {"file": "docs/pypi.md", "content-type": "text/markdown"}
    assert data["project"]["urls"] == {
        "Homepage": "https://github.com/mech-lab/blkbx-lab",
        "Documentation": "https://github.com/mech-lab/blkbx-lab/tree/main/docs",
        "Repository": "https://github.com/mech-lab/blkbx-lab",
        "Issues": "https://github.com/mech-lab/blkbx-lab/issues",
        "Changelog": "https://github.com/mech-lab/blkbx-lab/releases",
        "Validation Report": "https://github.com/mech-lab/blkbx-lab/blob/main/docs/research/qwen35-validation-report.md",
    }
    assert sorted(data["project"]["dependencies"]) == ["jsonschema>=4.23", "numpy>=2.0", "pyarrow>=17.0"]
    dependency_blob = " ".join(sorted(data["project"]["dependencies"])).lower()
    assert "torch" not in dependency_blob
    assert "transformers" not in dependency_blob
    assert "scipy" not in dependency_blob
    assert data["project"]["scripts"] == {"blkbx-lab": "blkbx_lab.cli:main"}
    assert data["tool"]["pytest"]["ini_options"] == {
        "testpaths": [
            "tests",
            "legacy/hybrid-mechlab-python/tests",
            "internal/trace/legacy_blt/tests",
            "internal/ink/legacy_mair/tests",
        ],
        "addopts": "-q --import-mode=importlib",
    }
    assert sorted(data["tool"]["setuptools"]["packages"]["find"]["include"]) == ["adapters*", "blkbx_lab*", "internal*"]
    assert sorted(data["tool"]["setuptools"]["packages"]["find"]["where"]) == ["."]
    assert sorted(data["tool"]["setuptools"]["packages"]["find"]["exclude"]) == ["legacy*"]
    assert data["tool"]["setuptools"]["package-data"] == {
        "hybrid_mechlab": ["py.typed", "_rust.pyi"],
        "blkbx_lab": ["py.typed"],
    }


def test_legacy_rust_package_uses_maturin():
    data = tomllib.loads((ROOT / "legacy" / "python-rust" / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["name"] == "hybrid-mechlab-rust"
    assert data["project"]["version"] == "0.1.0a2"
    assert data["build-system"]["build-backend"] == "maturin"
    assert data["tool"]["maturin"]["manifest-path"] == "../../rust/hm_pyo3/Cargo.toml"
