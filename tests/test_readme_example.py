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
    bundle = namespace["bundle"]
    assert bundle.manifest_path.endswith("mair_manifest.v1.json")
    assert Path(bundle.manifest_path).exists()
