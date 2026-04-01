from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BLT_SRC = ROOT / "internal" / "blt" / "src"
MAIR_SRC = ROOT / "internal" / "mair" / "src"

for path in (str(BLT_SRC), str(MAIR_SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)

from blt.export import run_trace
from hybrid_mechlab.cli import from_mair_main, topology_offline_main
from hybrid_mechlab.integrations.mair import load_trace_from_mair_manifest
from hybrid_mechlab.topology.offline import compute_persistence
from mair.validate import validate_artifact


def test_load_trace_from_mair_manifest_round_trips_blt_artifacts(tmp_path: Path) -> None:
    manifest_path = run_trace("Import this BLT trace.", "trace-hm-import", tmp_path, backend="mock")
    trace = load_trace_from_mair_manifest(str(manifest_path))
    report = compute_persistence(trace)

    assert trace.trace_id == "trace-hm-import"
    assert trace.backend == "mock"
    assert trace.profile.family.kind.value == "qwen35"
    assert report.trace_id == "trace-hm-import"
    assert report.backend == "mock"
    assert report.summary.h0_pairs >= 1
    assert report.summary.gluing_defect >= 0.0


def test_mair_cli_commands_write_exact_topology_artifacts(tmp_path: Path) -> None:
    manifest_path = run_trace("Export exact topology.", "trace-hm-cli", tmp_path / "run", backend="mock")
    trace_path = tmp_path / "trace.json"
    out_dir = tmp_path / "offline"

    assert from_mair_main([str(manifest_path), "--output-path", str(trace_path)]) == 0
    assert topology_offline_main([str(manifest_path), "--out-dir", str(out_dir)]) == 0

    trace_payload = json.loads(trace_path.read_text(encoding="utf-8"))
    topology_summary_path = out_dir / "topology_summary.v1.json"
    offline_report_path = out_dir / "offline_topology_report.v1.json"

    assert trace_payload["trace_id"] == "trace-hm-cli"
    assert trace_payload["backend"] == "mock"
    validate_artifact(topology_summary_path, "topology_summary")
    validate_artifact(offline_report_path, "offline_topology_report")

    topology_summary = json.loads(topology_summary_path.read_text(encoding="utf-8"))
    offline_report = json.loads(offline_report_path.read_text(encoding="utf-8"))
    assert topology_summary["topology_backend"] == "exact_persistence"
    assert offline_report["backend"] == "mock"
