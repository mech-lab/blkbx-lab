from __future__ import annotations

from pathlib import Path

import blkbx_lab as bl
from blkbx_lab.cli import main as blkbx_main
from blkbx_lab.objects import (
    ActionEvidenceBundle,
    DoctorResult,
    GateAnalysisResult,
    InkReceiptResult,
    ReceiptComparisonPacket,
)


def test_python_workflow_returns_public_objects(tmp_path: Path) -> None:
    bundle = bl.trace(
        "Capture a deterministic action proposal.",
        output_dir=tmp_path / "trace-left",
        trace_id="trace-left",
        backend="mock",
    )
    assert isinstance(bundle, ActionEvidenceBundle)
    assert Path(bundle.manifest_path).exists()

    analysis = bl.analyze(bundle.manifest_path, output_dir=tmp_path / "trace-left", profile="qwen3.5-hybrid")
    assert isinstance(analysis, GateAnalysisResult)
    assert Path(analysis.manifest_path).exists()
    assert analysis.risk_tier == "high"
    assert analysis.recommended_decision == "block"

    packet = bl.compare(left=analysis.manifest_path, right=analysis.manifest_path, output_dir=tmp_path / "compare")
    assert isinstance(packet, ReceiptComparisonPacket)
    assert Path(packet.comparison_path).exists()

    receipt = bl.gate(analysis.manifest_path, policy="action-gate")
    assert isinstance(receipt, InkReceiptResult)
    assert Path(receipt.receipt_path).exists()
    assert receipt.decision == "block"

    verified = bl.verify(receipt.receipt_path)
    assert verified.verification["valid"] is True
    assert "human_review_required" in bl.explain(receipt.receipt_path)
    assert bl.report(receipt.receipt_path) == f"Report for {receipt.receipt_path}"


def test_cli_verbs_work_end_to_end(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    demo_dir = tmp_path / "demo"
    trace_dir = tmp_path / "trace"
    compare_dir = tmp_path / "compare"

    assert blkbx_main(["demo", "qwen35-claims", "--output-dir", str(demo_dir)]) == 0
    assert blkbx_main(["doctor"]) == 0
    assert blkbx_main(["trace", "--prompt", "Capture a CLI trace.", "--backend", "mock", "--output-dir", str(trace_dir), "--trace-id", "trace-cli"]) == 0

    manifest_path = trace_dir / "ink_manifest.v1.json"
    assert blkbx_main(["analyze", str(manifest_path), "--output-dir", str(trace_dir), "--profile", "qwen3.5-hybrid"]) == 0
    assert blkbx_main(["compare", "--left", str(manifest_path), "--right", str(manifest_path), "--output-dir", str(compare_dir)]) == 0
    assert blkbx_main(["gate", str(manifest_path), "--policy", "action-gate"]) == 1
    assert blkbx_main(["verify", str(trace_dir / "ink_receipt.v1.json")]) == 0
    assert blkbx_main(["tamper", str(trace_dir / "ink_receipt.v1.json")]) == 0
    assert blkbx_main(["verify", str(trace_dir / "ink_receipt.tampered.json")]) == 1
    assert blkbx_main(["report", str(manifest_path), "--kind", "release-summary"]) == 0
    assert blkbx_main(["explain", str(trace_dir / "ink_receipt.v1.json")]) == 0


def test_demo_and_doctor_public_contract(tmp_path: Path) -> None:
    demo_result = bl.demo(output_dir=tmp_path / "demo-sdk")
    doctor_result = bl.doctor()

    assert isinstance(demo_result, InkReceiptResult)
    assert isinstance(doctor_result, DoctorResult)
    assert Path(demo_result.manifest_path).exists()
    assert Path(demo_result.receipt_path).exists()
    assert doctor_result.demo_ready is True
    assert doctor_result.real_replay_ready is False
