from __future__ import annotations

import json
from pathlib import Path

import blkbx_lab as bl
import pytest
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
    assert analysis.action_id == bundle.action_id
    assert analysis.risk_tier == "high"
    assert analysis.recommended_decision == "block"

    receipt = bl.gate(analysis.manifest_path, policy="action-gate")
    assert isinstance(receipt, InkReceiptResult)
    assert Path(receipt.receipt_path).exists()
    assert receipt.action_id == bundle.action_id
    assert receipt.decision == "block"

    packet = bl.compare(left=analysis.manifest_path, right=analysis.manifest_path, output_dir=tmp_path / "compare")
    assert isinstance(packet, ReceiptComparisonPacket)
    assert Path(packet.comparison_path).exists()
    assert packet.left_receipt_path == receipt.receipt_path
    comparison_payload = json.loads(Path(packet.comparison_path).read_text(encoding="utf-8"))
    assert comparison_payload["schema"] == "receipt.comparison.v1"
    assert comparison_payload["left_receipt_id"].startswith("ink_rcpt_")
    assert comparison_payload["decision_match"] is True
    assert comparison_payload["action_match"] is True

    verified = bl.verify(receipt.receipt_path)
    assert verified.verification["valid"] is True
    assert "human_review_required" in bl.explain(receipt.receipt_path)
    assert "BLKBX Lab Release Summary" in bl.report(receipt.receipt_path)
    assert "Decision: block" in bl.report(receipt.receipt_path)
    assert "BLKBX Lab Comparison Summary" in bl.report(packet.comparison_path)


def test_trace_accepts_public_qwen_aliases_and_rejects_unknown_ones(tmp_path: Path) -> None:
    alias_bundle = bl.trace(
        "Capture a deterministic action proposal.",
        output_dir=tmp_path / "trace-alias",
        model="Qwen/Qwen3.5-2B",
    )
    assert alias_bundle.summary["adapter"] == "qwen35"

    family_bundle = bl.trace(
        "Capture a deterministic action proposal.",
        output_dir=tmp_path / "trace-family",
        family="qwen3.5",
    )
    assert family_bundle.summary["adapter"] == "qwen35"

    with pytest.raises(ValueError, match="Supported public adapters: qwen35"):
        bl.trace("Capture a deterministic action proposal.", output_dir=tmp_path / "trace-invalid", model="unknown-model")


def test_compare_requires_a_sibling_receipt_for_manifest_targets(tmp_path: Path) -> None:
    bundle = bl.trace("Capture a deterministic action proposal.", output_dir=tmp_path / "trace")
    with pytest.raises(FileNotFoundError, match="Run blkbx-lab gate"):
        bl.compare(left=bundle.manifest_path, right=bundle.manifest_path, output_dir=tmp_path / "compare")


def test_experimental_report_kinds_fail_on_canonical_artifacts(tmp_path: Path) -> None:
    bundle = bl.trace("Capture a deterministic action proposal.", output_dir=tmp_path / "trace")
    with pytest.raises(ValueError, match="experimental and unavailable for canonical BLKBX artifacts"):
        bl.report(bundle, kind="tract-vs-bridge")


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
    assert blkbx_main(["gate", str(manifest_path), "--policy", "action-gate"]) == 1
    assert blkbx_main(["compare", "--left", str(manifest_path), "--right", str(manifest_path), "--output-dir", str(compare_dir)]) == 0
    assert blkbx_main(["verify", str(trace_dir / "ink_receipt.v1.json")]) == 0
    assert blkbx_main(["tamper", str(trace_dir / "ink_receipt.v1.json")]) == 0
    assert blkbx_main(["verify", str(trace_dir / "ink_receipt.tampered.json")]) == 1
    assert blkbx_main(["report", str(manifest_path), "--kind", "release-summary"]) == 0
    assert blkbx_main(["report", str(compare_dir / "receipt_comparison.v1.json"), "--kind", "comparison-summary"]) == 0
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
    assert "BLKBX Lab / Qwen3.5 Claims Demo" in demo_result.report
