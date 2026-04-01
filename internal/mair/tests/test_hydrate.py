from __future__ import annotations

from pathlib import Path

from mair.hydrate import iter_artifacts, load_artifact_bundle, load_artifact_by_type
from mair.manifest import write_manifest

from tests.support import write_full_artifact_set


def test_load_artifact_bundle_returns_manifest_and_payloads(tmp_path: Path) -> None:
    write_full_artifact_set(tmp_path)
    manifest_path = write_manifest(tmp_path, trace_id="trace-1", producer="mair:test:0.1.0")
    bundle = load_artifact_bundle(manifest_path)
    assert bundle["manifest"]["trace_id"] == "trace-1"
    assert "offline_topology_report" in bundle["artifacts"]
    assert "concept_lineage_bundle" in bundle["artifacts"]


def test_load_artifact_by_type_reads_parquet_as_rows(tmp_path: Path) -> None:
    write_full_artifact_set(tmp_path)
    manifest_path = write_manifest(tmp_path, trace_id="trace-1", producer="mair:test:0.1.0")
    rows = load_artifact_by_type(manifest_path, "blt_codes")
    assert isinstance(rows, list)
    assert rows[0]["trace_id"] == "trace-1"


def test_iter_artifacts_yields_all_present_artifacts(tmp_path: Path) -> None:
    write_full_artifact_set(tmp_path)
    manifest_path = write_manifest(tmp_path, trace_id="trace-1", producer="mair:test:0.1.0")
    artifact_types = [artifact_type for artifact_type, _payload in iter_artifacts(manifest_path)]
    assert "backend_comparison" in artifact_types
    assert "replacement_eval" in artifact_types
