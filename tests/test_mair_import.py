from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
BLT_SRC = ROOT / "internal" / "trace" / "legacy_blt" / "src"
MAIR_SRC = ROOT / "internal" / "ink" / "legacy_mair" / "src"


def _ensure_legacy_import_paths() -> None:
    for path in (str(BLT_SRC), str(MAIR_SRC)):
        if path not in sys.path:
            sys.path.insert(0, path)


def _load_legacy_symbols() -> SimpleNamespace:
    _ensure_legacy_import_paths()
    return SimpleNamespace(
        run_trace=importlib.import_module("blt.export").run_trace,
        from_mair_main=importlib.import_module("hybrid_mechlab.cli").from_mair_main,
        topology_offline_main=importlib.import_module("hybrid_mechlab.cli").topology_offline_main,
        load_trace_from_mair_manifest=importlib.import_module("hybrid_mechlab.integrations.mair").load_trace_from_mair_manifest,
        compute_persistence=importlib.import_module("hybrid_mechlab.topology.offline").compute_persistence,
        validate_artifact=importlib.import_module("mair.validate").validate_artifact,
    )


def test_load_trace_from_mair_manifest_round_trips_blt_artifacts(tmp_path: Path) -> None:
    modules = _load_legacy_symbols()
    manifest_path = modules.run_trace("Import this BLT trace.", "trace-hm-import", tmp_path, backend="mock")
    trace = modules.load_trace_from_mair_manifest(str(manifest_path))
    report = modules.compute_persistence(trace)

    assert trace.trace_id == "trace-hm-import"
    assert trace.backend == "mock"
    assert trace.profile.family.kind.value == "qwen35"
    assert report.trace_id == "trace-hm-import"
    assert report.backend == "mock"
    assert report.summary.h0_pairs >= 1
    assert report.summary.gluing_defect >= 0.0


def test_mair_cli_commands_write_exact_topology_artifacts(tmp_path: Path) -> None:
    modules = _load_legacy_symbols()
    manifest_path = modules.run_trace("Export exact topology.", "trace-hm-cli", tmp_path / "run", backend="mock")
    trace_path = tmp_path / "trace.json"
    out_dir = tmp_path / "offline"

    assert modules.from_mair_main([str(manifest_path), "--output-path", str(trace_path)]) == 0
    assert modules.topology_offline_main([str(manifest_path), "--out-dir", str(out_dir)]) == 0

    trace_payload = json.loads(trace_path.read_text(encoding="utf-8"))
    topology_summary_path = out_dir / "topology_summary.v1.json"
    offline_report_path = out_dir / "offline_topology_report.v1.json"

    assert trace_payload["trace_id"] == "trace-hm-cli"
    assert trace_payload["backend"] == "mock"
    modules.validate_artifact(topology_summary_path, "topology_summary")
    modules.validate_artifact(offline_report_path, "offline_topology_report")

    topology_summary = json.loads(topology_summary_path.read_text(encoding="utf-8"))
    offline_report = json.loads(offline_report_path.read_text(encoding="utf-8"))
    assert topology_summary["topology_backend"] == "exact_persistence"
    assert offline_report["backend"] == "mock"
