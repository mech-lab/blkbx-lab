from __future__ import annotations

from pathlib import Path

import mech_lab as ml
from mech_lab.cli import main as mechlab_main
from mech_lab.objects import AnalysisResult, ComparisonPacket, DoctorResult, EvidenceBundle, ReceiptResult


REQUIRED_HOOKS = {"pre-D1", "post-D1", "post-D2", "post-D3", "post-attention", "block-output"}


def test_python_workflow_returns_public_objects(tmp_path: Path) -> None:
    bundle = ml.trace(
        "Measure bridge dependence for a deterministic mock trace.",
        output_dir=tmp_path / "trace-left",
        trace_id="trace-left",
        backend="mock",
    )
    assert isinstance(bundle, EvidenceBundle)
    assert Path(bundle.manifest_path).exists()

    analysis = ml.analyze(bundle, output_dir=tmp_path / "trace-left", profile="qwen3.5-hybrid")
    assert isinstance(analysis, AnalysisResult)
    assert Path(analysis.manifest_path).exists()
    assert analysis.summary["hook_validation"]["passed"] is True

    packet = ml.compare(left=analysis, right=analysis, output_dir=tmp_path / "compare")
    assert isinstance(packet, ComparisonPacket)
    assert Path(packet.comparison_path).exists()

    receipt = ml.gate(analysis, policy="release-assurance")
    assert isinstance(receipt, ReceiptResult)
    assert Path(receipt.receipt_path).exists()

    assert "mech-lab Release Summary" in ml.report(analysis)
    assert "mech-lab Comparison Packet" in ml.report(packet, kind="comparison-summary")
    assert "passed" in ml.explain(receipt).lower()


def test_cli_verbs_work_end_to_end(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    demo_dir = tmp_path / "demo"
    trace_dir = tmp_path / "trace"
    compare_dir = tmp_path / "compare"

    assert mechlab_main(["demo", "--output-dir", str(demo_dir), "--trace-id", "trace-demo-cli"]) == 0
    assert mechlab_main(["doctor"]) == 0
    assert mechlab_main(["trace", "--prompt", "Capture a CLI trace.", "--backend", "mock", "--output-dir", str(trace_dir), "--trace-id", "trace-cli"]) == 0

    manifest_path = trace_dir / "mair_manifest.v1.json"
    assert mechlab_main(["analyze", str(manifest_path), "--output-dir", str(trace_dir), "--profile", "qwen3.5-hybrid"]) == 0
    analyzed_manifest = trace_dir / "mair_manifest.v1.json"
    assert mechlab_main(["compare", "--left", str(analyzed_manifest), "--right", str(analyzed_manifest), "--output-dir", str(compare_dir)]) == 0
    assert mechlab_main(["gate", str(analyzed_manifest), "--policy", "release-assurance"]) == 0
    assert mechlab_main(["report", str(analyzed_manifest), "--kind", "tract-vs-bridge"]) == 0
    assert mechlab_main(["report", str(compare_dir / "backend_comparison.v1.json"), "--kind", "comparison-summary"]) == 0
    assert mechlab_main(["explain", str(trace_dir / "assurance_receipt.v1.json")]) == 0


def test_qwen_product_lane_maps_to_required_hooks(tmp_path: Path) -> None:
    bundle = ml.trace(
        "Map the Qwen product lane without real replay.",
        output_dir=tmp_path / "qwen-mock",
        trace_id="trace-qwen-mock",
        backend="mock",
        family="qwen3.5",
        model="qwen3.5-2b",
    )
    analysis = ml.analyze(bundle, output_dir=tmp_path / "qwen-mock", profile="qwen3.5-hybrid")

    assert analysis.summary["model_family"] == "qwen3.5-hybrid"
    assert REQUIRED_HOOKS.issubset(set(analysis.summary["hook_validation"]["available"]))
    assert analysis.summary["hook_validation"]["missing"] == []
    assert {"bridge-necessity", "compression-forgetting", "tract-vs-bridge"}.issubset(set(analysis.report_kinds))


def test_demo_and_doctor_public_contract(tmp_path: Path) -> None:
    demo_result = ml.demo(output_dir=tmp_path / "demo-sdk")
    doctor_result = ml.doctor()

    assert isinstance(demo_result, AnalysisResult)
    assert isinstance(doctor_result, DoctorResult)
    assert Path(demo_result.manifest_path).exists()
    assert demo_result.receipt_path is not None
    assert Path(demo_result.receipt_path).exists()
    assert doctor_result.demo_ready is True
