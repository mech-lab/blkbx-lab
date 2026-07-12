from __future__ import annotations

from dataclasses import dataclass, field
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
class EvidenceBundle:
    trace_id: str
    manifest_path: str
    output_dir: str
    summary: dict[str, Any]
    report: str
    bundle_digest: str
    receipt_path: str | None = None
    report_kinds: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "manifest_path": self.manifest_path,
            "output_dir": self.output_dir,
            "summary": self.summary,
            "report": self.report,
            "bundle_digest": self.bundle_digest,
            "receipt_path": self.receipt_path,
            "report_kinds": list(self.report_kinds),
        }


@dataclass(slots=True)
class AnalysisResult:
    trace_id: str
    manifest_path: str
    output_dir: str
    summary: dict[str, Any]
    report: str
    bundle_digest: str
    profile: str | None
    receipt_path: str | None = None
    report_kinds: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "manifest_path": self.manifest_path,
            "output_dir": self.output_dir,
            "summary": self.summary,
            "report": self.report,
            "bundle_digest": self.bundle_digest,
            "profile": self.profile,
            "receipt_path": self.receipt_path,
            "report_kinds": list(self.report_kinds),
        }


@dataclass(slots=True)
class ComparisonPacket:
    comparison_path: str
    output_dir: str
    left_manifest_path: str
    right_manifest_path: str
    summary: dict[str, Any]
    report: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "comparison_path": self.comparison_path,
            "output_dir": self.output_dir,
            "left_manifest_path": self.left_manifest_path,
            "right_manifest_path": self.right_manifest_path,
            "summary": self.summary,
            "report": self.report,
        }


@dataclass(slots=True)
class ReceiptResult:
    trace_id: str
    receipt_path: str
    manifest_path: str
    decision: str
    summary: dict[str, Any]
    report: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "receipt_path": self.receipt_path,
            "manifest_path": self.manifest_path,
            "decision": self.decision,
            "summary": self.summary,
            "report": self.report,
        }


PublicArtifact = EvidenceBundle | AnalysisResult | ComparisonPacket | ReceiptResult
PublicTarget = str | Path | PublicArtifact
