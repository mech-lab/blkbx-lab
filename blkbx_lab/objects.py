from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DoctorResult:
    status: str
    checks: list[dict[str, Any]]
    notes: list[str]
    demo_ready: bool
    real_replay_ready: bool
    report: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "checks": self.checks,
            "notes": self.notes,
            "demo_ready": self.demo_ready,
            "real_replay_ready": self.real_replay_ready,
            "report": self.report,
        }


@dataclass(slots=True)
class ActionEvidenceBundle:
    action_id: str
    manifest_path: str
    output_dir: str
    summary: dict[str, Any]
    report: str
    evidence_hashes: list[str]
    receipt_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "manifest_path": self.manifest_path,
            "output_dir": self.output_dir,
            "summary": self.summary,
            "report": self.report,
            "evidence_hashes": self.evidence_hashes,
            "receipt_path": self.receipt_path,
        }


@dataclass(slots=True)
class GateAnalysisResult:
    action_id: str
    manifest_path: str
    output_dir: str
    risk_tier: str
    required_controls: list[str]
    missing_controls: list[str]
    recommended_decision: str
    summary: dict[str, Any]
    report: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "manifest_path": self.manifest_path,
            "output_dir": self.output_dir,
            "risk_tier": self.risk_tier,
            "required_controls": self.required_controls,
            "missing_controls": self.missing_controls,
            "recommended_decision": self.recommended_decision,
            "summary": self.summary,
            "report": self.report,
        }


@dataclass(slots=True)
class InkReceiptResult:
    action_id: str
    receipt_path: str
    manifest_path: str
    decision: str
    summary: dict[str, Any]
    verification: dict[str, Any]
    report: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "receipt_path": self.receipt_path,
            "manifest_path": self.manifest_path,
            "decision": self.decision,
            "summary": self.summary,
            "verification": self.verification,
            "report": self.report,
        }


@dataclass(slots=True)
class ReceiptComparisonPacket:
    comparison_path: str
    output_dir: str
    left_receipt_path: str
    right_receipt_path: str
    summary: dict[str, Any]
    report: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparison_path": self.comparison_path,
            "output_dir": self.output_dir,
            "left_receipt_path": self.left_receipt_path,
            "right_receipt_path": self.right_receipt_path,
            "summary": self.summary,
            "report": self.report,
        }


PublicArtifact = ActionEvidenceBundle | GateAnalysisResult | ReceiptComparisonPacket | InkReceiptResult
PublicTarget = str | Path | PublicArtifact
