from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("blt")
pytest.importorskip("mair.validate")

from blt.export import run_analysis, run_trace
from mair.validate import validate_manifest


def test_run_analysis_adds_grouped_clt_and_interventions(tmp_path: Path) -> None:
    manifest_path = run_trace("Map bridge tract signal.", "trace-blt-2", tmp_path, backend="mock")
    manifest_path = run_analysis(manifest_path)
    payload = validate_manifest(manifest_path)
    names = {artifact["artifact_type"] for artifact in payload["artifacts"]}
    assert "grouped_clt_bundle" in names
    assert "intervention_sweep" in names
    bundle = json.loads((tmp_path / "grouped_clt_bundle.v1.json").read_text(encoding="utf-8"))
    assert bundle["groups"]
