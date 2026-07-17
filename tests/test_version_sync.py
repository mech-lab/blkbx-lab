import json
import tomllib
from pathlib import Path

from blkbx_lab._version import __version__


ROOT = Path(__file__).resolve().parents[1]


def _toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def test_python_versions_are_synced_for_v1_release():
    root_project = _toml(ROOT / "pyproject.toml")
    root_version = root_project["project"]["version"]

    assert __version__ == root_version


def test_workspace_crates_share_the_v1_release_version():
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
        "ink-receipt-v2",
        "ink-tui",
        "ink-vectors",
        "ink-verify",
        "ink-wasm",
    }
    versions = {_toml(path)["package"]["version"]["workspace"] for path in cargo_paths}
    assert versions == {True}


def test_source_slice_manifests_track_the_root_release_version():
    root_version = _toml(ROOT / "pyproject.toml")["project"]["version"]
    assert _toml(ROOT / "products" / "due-sdk" / "pyproject.toml")["project"]["version"] == root_version
    assert _toml(ROOT / "products" / "mand8-sdk" / "pyproject.toml")["project"]["version"] == root_version

    due_package = json.loads((ROOT / "products" / "due-sdk" / "package.json").read_text(encoding="utf-8"))
    mand8_package = json.loads((ROOT / "products" / "mand8-sdk" / "package.json").read_text(encoding="utf-8"))
    assert due_package["version"] == root_version
    assert mand8_package["version"] == root_version
