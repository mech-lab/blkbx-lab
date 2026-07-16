from __future__ import annotations

import json
import warnings
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
        adapter="qwen35",
    )
    assert isinstance(bundle, ActionEvidenceBundle)
    assert Path(bundle.manifest_path).exists()

    analysis = bl.analyze(bundle.manifest_path, output_dir=tmp_path / "trace-left")
    assert isinstance(analysis, GateAnalysisResult)
    assert Path(analysis.manifest_path).exists()
    assert analysis.action_id == bundle.action_id
    assert analysis.risk_tier == "low"
    assert analysis.recommended_decision == "pass"

    receipt = bl.gate(analysis.manifest_path, demo_signer=True)
    assert isinstance(receipt, InkReceiptResult)
    assert Path(receipt.receipt_path).exists()
    assert receipt.action_id == bundle.action_id
    assert receipt.decision == "pass"

    packet = bl.compare(left=analysis.manifest_path, right=analysis.manifest_path, output_dir=tmp_path / "compare")
    assert isinstance(packet, ReceiptComparisonPacket)
    assert Path(packet.comparison_path).exists()
    assert packet.left_receipt_path == receipt.receipt_path
    comparison_payload = json.loads(Path(packet.comparison_path).read_text(encoding="utf-8"))
    assert comparison_payload["schema"] == "receipt.comparison.v2"
    assert comparison_payload["left_receipt_id"].startswith("urn:ink:receipt:")
    assert comparison_payload["decision_match"] is True
    assert comparison_payload["action_match"] is True

    verified = bl.verify(receipt.receipt_path)
    assert verified.verification["valid"] is True
    assert verified.verification["overall"] == "pass"
    assert "RUNTIME_DETERMINISTIC_DEMO" in bl.explain(receipt.receipt_path)
    assert "Verification for" in bl.report(receipt.receipt_path)
    assert "Decision: pass" in bl.report(receipt.receipt_path)
    assert "BLKBX Lab Comparison Summary" in bl.report(packet.comparison_path)


def test_legacy_public_aliases_warn_but_still_normalize(tmp_path: Path) -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        alias_bundle = bl.trace(
            "Capture a deterministic action proposal.",
            output_dir=tmp_path / "trace-alias",
            model="Qwen/Qwen3.5-2B",
        )
        family_bundle = bl.trace(
            "Capture a deterministic action proposal.",
            output_dir=tmp_path / "trace-family",
            family="qwen3.5",
        )
        backend_bundle = bl.trace(
            "Capture a deterministic action proposal.",
            output_dir=tmp_path / "trace-backend",
            backend="mock",
        )
        analysis = bl.analyze(
            backend_bundle.manifest_path,
            output_dir=tmp_path / "trace-backend",
            profile="qwen3.5-hybrid",
        )

    assert alias_bundle.summary["adapter"] == "qwen35"
    assert family_bundle.summary["adapter"] == "qwen35"
    assert analysis.recommended_decision == "pass"
    messages = [str(w.message) for w in caught]
    assert any("normalized to the `qwen35` deterministic demo adapter" in message for message in messages)
    assert any("ignored in the canonical v0.7 thin-waist flow" in message for message in messages)

    with pytest.raises(ValueError, match="Supported public adapters: qwen35"):
        bl.trace(
            "Capture a deterministic action proposal.",
            output_dir=tmp_path / "trace-invalid",
            model="unknown-model",
        )


def test_compare_requires_a_sibling_receipt_for_manifest_targets(tmp_path: Path) -> None:
    bundle = bl.trace("Capture a deterministic action proposal.", output_dir=tmp_path / "trace")
    with pytest.raises(FileNotFoundError, match="Run blkbx-lab gate"):
        bl.compare(left=bundle.manifest_path, right=bundle.manifest_path, output_dir=tmp_path / "compare")


def test_experimental_report_kinds_fail_on_canonical_artifacts(tmp_path: Path) -> None:
    bundle = bl.trace("Capture a deterministic action proposal.", output_dir=tmp_path / "trace")
    with pytest.raises(ValueError, match="experimental and unavailable for canonical BLKBX artifacts"):
        bl.report(bundle, kind="tract-vs-bridge")


def test_gate_requires_explicit_demo_signer(tmp_path: Path) -> None:
    bundle = bl.trace(
        "Capture a deterministic action proposal.",
        output_dir=tmp_path / "trace-gate",
        adapter="qwen35",
    )
    with pytest.raises(Exception, match="demo signer"):
        bl.gate(bundle.manifest_path)
    receipt = bl.gate(bundle.manifest_path, demo_signer=True)
    assert Path(receipt.receipt_path).exists()


def test_cli_verbs_work_end_to_end(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    demo_dir = tmp_path / "demo"
    trace_dir = tmp_path / "trace"
    compare_dir = tmp_path / "compare"

    assert blkbx_main(["demo", "qwen35", "--output-dir", str(demo_dir)]) == 0
    assert blkbx_main(["doctor"]) == 0
    assert blkbx_main(["trace", "--prompt", "Capture a CLI trace.", "--adapter", "qwen35", "--output-dir", str(trace_dir), "--trace-id", "trace-cli"]) == 0

    manifest_path = trace_dir / "ink_manifest.v2.json"
    assert blkbx_main(["analyze", str(manifest_path), "--output-dir", str(trace_dir)]) == 0
    assert blkbx_main(["gate", str(manifest_path), "--demo-signer"]) == 0
    assert blkbx_main(["compare", "--left", str(manifest_path), "--right", str(manifest_path), "--output-dir", str(compare_dir)]) == 0
    assert blkbx_main(["verify", str(trace_dir / "ink_receipt.v2.json")]) == 0
    assert blkbx_main(["tamper", str(trace_dir / "ink_receipt.v2.json")]) == 0
    assert blkbx_main(["verify", str(trace_dir / "ink_receipt.tampered.v2.json")]) == 1
    assert blkbx_main(["report", str(manifest_path), "--kind", "release-summary"]) == 0
    assert blkbx_main(["report", str(compare_dir / "receipt_comparison.v2.json"), "--kind", "comparison-summary"]) == 0
    assert blkbx_main(["explain", str(trace_dir / "ink_receipt.v2.json")]) == 0


def test_demo_and_doctor_public_contract(tmp_path: Path) -> None:
    demo_result = bl.demo(output_dir=tmp_path / "demo-sdk")
    doctor_result = bl.doctor()

    assert isinstance(demo_result, InkReceiptResult)
    assert isinstance(doctor_result, DoctorResult)
    assert Path(demo_result.manifest_path).exists()
    assert Path(demo_result.receipt_path).exists()
    assert doctor_result.demo_ready is True
    assert doctor_result.real_replay_ready is False
    assert "BLKBX Lab / qwen35 Demo" in demo_result.report
