import json
from pathlib import Path

from hybrid_mechlab import HybridLab, profiles
from hybrid_mechlab.io import jsonl
from hybrid_mechlab.topology.offline import (
    compare_persistence,
    compute_persistence,
    export_persistence_comparison,
    export_persistence_report,
    export_trace_and_persistence_artifacts,
)


def _canonical_traces():
    qwen_trace = HybridLab.attach(
        model="dummy-qwen",
        profile=profiles.reference.qwen35(),
        backend="adapter",
    ).run(prompts=["Measure topology for a reference hybrid."])
    gated_trace = HybridLab.attach(
        model="dummy-native",
        profile=profiles.native.gated_deltanet(),
        backend="native",
    ).run(prompts=["Measure topology for a native kernel."])
    return qwen_trace, gated_trace


def test_compute_persistence_returns_typed_reports():
    qwen_trace, gated_trace = _canonical_traces()
    qwen_report = compute_persistence(qwen_trace)
    gated_report = compute_persistence(gated_trace)
    assert qwen_report.family == "qwen35"
    assert gated_report.family == "gated_deltanet"
    assert qwen_report.summary.h0_pairs >= 1
    assert gated_report.summary.h0_pairs >= 1


def test_compare_persistence_reports_summary_deltas():
    qwen_trace, gated_trace = _canonical_traces()
    comparison = compare_persistence(qwen_trace, gated_trace)
    assert comparison.family_pair == ("qwen35", "gated_deltanet")
    assert isinstance(comparison.max_finite_persistence_delta, float)
    assert isinstance(comparison.gluing_defect_delta, float)


def test_json_artifact_exports_have_stable_shape(tmp_path):
    qwen_trace, gated_trace = _canonical_traces()
    qwen_report = compute_persistence(qwen_trace)
    comparison = compare_persistence(qwen_report, compute_persistence(gated_trace))

    report_path = tmp_path / "qwen.persistence.json"
    comparison_path = tmp_path / "qwen-vs-gated.comparison.json"
    export_persistence_report(qwen_report, str(report_path))
    export_persistence_comparison(comparison, str(comparison_path))

    report_record = jsonl.load(str(report_path))
    comparison_record = jsonl.load(str(comparison_path))
    assert sorted(report_record.keys()) == [
        "backend",
        "diagrams",
        "family",
        "persistence_input",
        "profile_name",
        "summary",
        "trace_id",
    ]
    assert sorted(comparison_record.keys()) == [
        "backend_pair",
        "bridge_dependence_delta",
        "family_pair",
        "gluing_defect_delta",
        "left_summary",
        "left_trace_id",
        "max_finite_persistence_delta",
        "right_summary",
        "right_trace_id",
        "topology_drift_delta",
        "total_finite_persistence_delta",
        "tract_retention_delta",
    ]


def test_trace_and_persistence_artifacts_are_blt_consumable(tmp_path):
    qwen_trace, _ = _canonical_traces()
    paths = export_trace_and_persistence_artifacts(qwen_trace, str(tmp_path))
    persistence_record = json.loads(Path(paths["persistence"]).read_text(encoding="utf-8"))
    assert "family" in persistence_record
    assert "backend" in persistence_record
    assert "diagrams" in persistence_record
    assert "summary" in persistence_record
