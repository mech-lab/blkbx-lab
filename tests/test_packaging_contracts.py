import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_root_package_is_mech_lab_and_numpy_only():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["build-system"]["build-backend"] == "setuptools.build_meta"
    assert data["project"]["name"] == "mech-lab"
    assert data["project"]["version"] == "0.1.0a1"
    assert data["project"]["dependencies"] == ["numpy>=2.0"]
    dependency_blob = " ".join(data["project"]["dependencies"]).lower()
    assert "torch" not in dependency_blob
    assert "transformers" not in dependency_blob
    assert "scipy" not in dependency_blob
    assert data["project"]["scripts"] == {"mechlab": "mech_lab.cli:main"}
    assert sorted(data["tool"]["setuptools"]["packages"]["find"]["include"]) == ["hybrid_mechlab*", "mech_lab*"]


def test_companion_rust_package_uses_maturin():
    data = tomllib.loads((ROOT / "python-rust" / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["name"] == "hybrid-mechlab-rust"
    assert data["project"]["version"] == "0.1.0a1"
    assert data["build-system"]["build-backend"] == "maturin"
    assert data["tool"]["maturin"]["manifest-path"] == "../rust/hm_pyo3/Cargo.toml"
