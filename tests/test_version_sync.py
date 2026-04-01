import tomllib
from pathlib import Path

from hybrid_mechlab._version import RUST_CORE_VERSION, __version__


ROOT = Path(__file__).resolve().parents[1]


def _toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def test_python_versions_are_synced():
    root_project = _toml(ROOT / "pyproject.toml")
    rust_project = _toml(ROOT / "python-rust" / "pyproject.toml")

    assert root_project["project"]["version"] == "0.1.0a1"
    assert __version__ == "0.1.0a1"
    assert rust_project["project"]["version"] == "0.1.0a1"


def test_cargo_versions_are_synced():
    cargo_paths = (
        ROOT / "rust" / "hm_core" / "Cargo.toml",
        ROOT / "rust" / "hm_std" / "Cargo.toml",
        ROOT / "rust" / "hm_liger" / "Cargo.toml",
        ROOT / "rust" / "hm_pyo3" / "Cargo.toml",
        ROOT / "rust" / "hm_examples" / "Cargo.toml",
    )
    versions = {_toml(path)["package"]["version"] for path in cargo_paths}
    assert versions == {"0.1.0-alpha.1"}
    assert RUST_CORE_VERSION == "0.1.0-alpha.1"
