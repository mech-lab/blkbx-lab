import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_root_package_is_mech_lab_and_numpy_only():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["build-system"]["build-backend"] == "setuptools.build_meta"
    assert data["project"]["name"] == "mech-lab"
    assert data["project"]["version"] == "0.1.0a1"
    assert sorted(data["project"]["dependencies"]) == ["jsonschema>=4.23", "numpy>=2.0", "pyarrow>=17.0"]
    dependency_blob = " ".join(sorted(data["project"]["dependencies"])).lower()
    assert "torch" not in dependency_blob
    assert "transformers" not in dependency_blob
    assert "scipy" not in dependency_blob
    assert data["project"]["scripts"] == {"mechlab": "mech_lab.cli:main"}
    assert sorted(data["tool"]["setuptools"]["packages"]["find"]["include"]) == ["blt*", "hybrid_mechlab*", "mair*", "mech_lab*"]
    assert sorted(data["tool"]["setuptools"]["packages"]["find"]["where"]) == [".", "internal/blt/src", "internal/mair/src"]
    assert sorted(data["tool"]["setuptools"]["packages"]["find"]["exclude"]) == ["internal*", "legacy*"]
    assert data["tool"]["setuptools"]["package-data"]["blt"] == ["configs/*.json", "configs/*.md"]
    assert data["tool"]["setuptools"]["package-data"]["mair"] == ["schemas/*.json"]


def test_legacy_rust_package_uses_maturin():
    data = tomllib.loads((ROOT / "legacy" / "python-rust" / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["name"] == "hybrid-mechlab-rust"
    assert data["project"]["version"] == "0.1.0a1"
    assert data["build-system"]["build-backend"] == "maturin"
    assert data["tool"]["maturin"]["manifest-path"] == "../../rust/hm_pyo3/Cargo.toml"
