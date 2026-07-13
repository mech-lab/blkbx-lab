import tomllib
from pathlib import Path

from blkbx_lab._version import __version__


ROOT = Path(__file__).resolve().parents[1]


def _toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def test_python_versions_are_synced_for_v06_release():
    root_project = _toml(ROOT / "pyproject.toml")

    assert root_project["project"]["version"] == "0.6.0"
    assert __version__ == "0.6.0"


def test_workspace_crates_share_the_v06_release_version():
    workspace = _toml(ROOT / "Cargo.toml")
    assert workspace["workspace"]["package"]["version"] == "0.6.0"
    cargo_paths = (
        ROOT / "rust" / "crates" / "ink-core" / "Cargo.toml",
        ROOT / "rust" / "crates" / "ink-host" / "Cargo.toml",
        ROOT / "rust" / "crates" / "ink-py" / "Cargo.toml",
    )
    versions = {_toml(path)["package"]["version"]["workspace"] for path in cargo_paths}
    assert versions == {True}
