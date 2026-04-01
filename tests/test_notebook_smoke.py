import json
import sys
from pathlib import Path


ROOT = Path("/Volumes/128/hybridTDA")


def _execute_notebook(path: Path, tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    notebook = json.loads(path.read_text(encoding="utf-8"))
    namespace = {"__name__": "__notebook__"}
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        exec(source, namespace, namespace)


def test_qwen_attach_notebook_executes(tmp_path, monkeypatch):
    _execute_notebook(ROOT / "notebooks" / "00_qwen35_attach.ipynb", tmp_path, monkeypatch)
    assert (tmp_path / "artifacts" / "qwen35_attach").exists()


def test_qwen_vs_gated_comparison_notebook_executes(tmp_path, monkeypatch):
    _execute_notebook(ROOT / "notebooks" / "04_ratio_comparison.ipynb", tmp_path, monkeypatch)
    assert (tmp_path / "artifacts" / "qwen_vs_gated" / "comparison.json").exists()
