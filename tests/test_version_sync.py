import tomllib
from pathlib import Path

from blkbx_lab._version import __version__


ROOT = Path(__file__).resolve().parents[1]


def _toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def test_python_versions_are_synced_for_v09_release():
    root_project = _toml(ROOT / "pyproject.toml")
    root_version = root_project["project"]["version"]

    assert __version__ == root_version


def test_workspace_crates_share_the_v09_release_version():
    root_project = _toml(ROOT / "pyproject.toml")
    root_version = root_project["project"]["version"]
    workspace = _toml(ROOT / "Cargo.toml")
    assert workspace["workspace"]["package"]["version"] == root_version
    cargo_paths = sorted((ROOT / "rust" / "crates").glob("*/Cargo.toml"))
    crate_names = {_toml(path)["package"]["name"] for path in cargo_paths}
    assert crate_names == {
        "ink-cli",
        "ink-core",
        "ink-host",
        "ink-py",
        "ink-vectors",
        "ink-verify",
        "ink-wasm",
    }
    versions = {_toml(path)["package"]["version"]["workspace"] for path in cargo_paths}
    assert versions == {True}
