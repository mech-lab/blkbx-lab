from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _first_python_block(readme: str) -> str:
    marker = "```python\n"
    start = readme.index(marker) + len(marker)
    end = readme.index("\n```", start)
    return readme[start:end]


def test_readme_quickstart_example_executes(tmp_path, monkeypatch):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    source = _first_python_block(readme)
    monkeypatch.chdir(tmp_path)
    namespace = {"__name__": "__readme__"}
    exec(source, namespace, namespace)
    result = namespace["result"]
    assert result.manifest_path.endswith("ink_manifest.v1.json")
    assert result.receipt_path.endswith("ink_receipt.v1.json")
    assert Path(result.manifest_path).exists()
    assert Path(result.receipt_path).exists()
