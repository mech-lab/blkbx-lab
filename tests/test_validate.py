from __future__ import annotations

from pathlib import Path

from mair.manifest import write_manifest
from mair.validate import validate_artifact, validate_manifest

from tests.support import write_full_artifact_set


def test_validate_artifact_roundtrip(tmp_path: Path) -> None:
    write_full_artifact_set(tmp_path)
    validate_artifact(tmp_path / "mair_graph_ir.v1.json")
    validate_artifact(tmp_path / "offline_topology_report.v1.json")
    validate_artifact(tmp_path / "backend_comparison.v1.json")
    validate_artifact(tmp_path / "replacement_eval.v1.json")
    validate_artifact(tmp_path / "concept_lineage_bundle.v1.json")
    validate_artifact(tmp_path / "blt_codes.v1.parquet")
    validate_artifact(tmp_path / "mair_semantic_trace.v1.jsonl")


def test_validate_manifest_walks_all_artifacts(tmp_path: Path) -> None:
    write_full_artifact_set(tmp_path)
    manifest_path = write_manifest(tmp_path, trace_id="trace-1", producer="mair:test:0.1.0")
    payload = validate_manifest(manifest_path)
    assert payload["trace_id"] == "trace-1"
    assert len(payload["artifacts"]) == 13
