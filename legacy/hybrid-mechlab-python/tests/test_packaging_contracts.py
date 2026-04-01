import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_repo_is_python_only_and_numpy_only():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["name"] == "hybrid-mechlab-python"
    assert data["project"]["version"] == "0.1.0a1"
    assert data["project"]["dependencies"] == ["numpy>=2.0"]
    assert "optional-dependencies" in data["project"]
    assert "rust" not in data["project"]["optional-dependencies"]
