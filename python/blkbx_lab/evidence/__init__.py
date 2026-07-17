from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import json
from importlib.resources import files
from jsonschema import Draft7Validator, FormatChecker

# Load schemas
SCHEMA_FILES = {
    "ink.evidence.record.v1": "ink.evidence.record.v1.schema.json",
    "ink.evidence.requirement.v1": "ink.evidence.requirement.v1.schema.json",
    "ink.evidence.gap.v1": "ink.evidence.gap.v1.schema.json",
    "ink.document_evidence.v1": "ink.document_evidence.v1.schema.json",
    "ink.attestation.v1": "ink.attestation.v1.schema.json",
    "ink.reviewer_profile.v1": "ink.reviewer_profile.v1.schema.json",
    "ink.redaction_profile.v1": "ink.redaction_profile.v1.schema.json",
    "ink.retention_profile.v1": "ink.retention_profile.v1.schema.json",
}

def load_schema(schema_name: str) -> dict:
    filename = SCHEMA_FILES.get(schema_name)
    if not filename:
        raise ValueError(f"Unknown schema: {schema_name}")
    return json.loads(files("blkbx_lab.schemas").joinpath(filename).read_text(encoding="utf-8"))

def validate(payload: dict, schema_name: str = None) -> bool:
    name = schema_name or payload.get("schema")
    if not name:
        raise ValueError("schema_name required when payload lacks schema field")
    validator = Draft7Validator(load_schema(name), format_checker=FormatChecker())
    validator.validate(payload)
    return True

@dataclass
class EvidenceRecord:
    record_id: str
    product: str
    action: str
    model: str
    input_commitments: dict[str, Any] = None
    output_commitments: dict[str, Any] = None
    policy_binding: dict[str, Any] = None
    control_evidence: list[dict[str, Any]] = None
    evaluation_evidence: list[dict[str, Any]] = None
    exception_evidence: list[dict[str, Any]] = None
    incident_evidence: list[dict[str, Any]] = None
    human_authority: dict[str, Any] = None
    disclosure_profile: dict[str, Any] = None
    integrity_provenance: dict[str, Any] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "ink.evidence.record.v1",
            "record_id": self.record_id,
            "product": self.product,
            "action": self.action,
            "model": self.model,
            "input_commitments": self.input_commitments or {},
            "output_commitments": self.output_commitments or {},
            "policy_binding": self.policy_binding or {},
            "control_evidence": self.control_evidence or [],
            "evaluation_evidence": self.evaluation_evidence or [],
            "exception_evidence": self.exception_evidence or [],
            "incident_evidence": self.incident_evidence or [],
            "human_authority": self.human_authority or {},
            "disclosure_profile": self.disclosure_profile or {},
            "integrity_provenance": self.integrity_provenance or {},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceRecord":
        record = data.copy()
        record_id = record.pop("record_id", "")
        return cls(record_id=record_id, **record)

@dataclass
class EvidenceRequirement:
    requirement_id: str
    vertical: str
    artifact_type: str
    support_type: str  # machine_verifiable, document_verifiable, attestation_required
    coverage_status: str  # covered, missing, stale, insufficient, reviewer_specific
    reviewer_profiles: list[str] = None
    mapped_receipts: list[str] = None
    mapped_documents: list[str] = None
    mapped_attestations: list[str] = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "ink.evidence.requirement.v1",
            "requirement_id": self.requirement_id,
            "vertical": self.vertical,
            "artifact_type": self.artifact_type,
            "support_type": self.support_type,
            "coverage_status": self.coverage_status,
            "reviewer_profiles": self.reviewer_profiles or [],
            "mapped_receipts": self.mapped_receipts or [],
            "mapped_documents": self.mapped_documents or [],
            "mapped_attestations": self.mapped_attestations or [],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceRequirement":
        req = data.copy()
        return cls(**req)

@dataclass
class EvidenceGap:
    gap_id: str
    requirement_id: str
    gap_type: str  # missing, stale, insufficient, reviewer_specific
    missing_source: str
    severity: str
    reviewer_importance: str
    remediation_path: str
    estimated_effort: str
    bundle_blocking: bool = False
    stale_after: str = ""
    notes: str = ""
    mapped_requirements: list[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "ink.evidence.gap.v1",
            "gap_id": self.gap_id,
            "requirement_id": self.requirement_id,
            "gap_type": self.gap_type,
            "missing_source": self.missing_source,
            "severity": self.severity,
            "reviewer_importance": self.reviewer_importance,
            "remediation_path": self.remediation_path,
            "estimated_effort": self.estimated_effort,
            "bundle_blocking": self.bundle_blocking,
            "stale_after": self.stale_after,
            "notes": self.notes,
            "mapped_requirements": self.mapped_requirements or [],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EvidenceGap":
        gap = data.copy()
        return cls(**gap)

@dataclass
class DocumentEvidence:
    source_id: str
    content_hash: str
    metadata: dict[str, Any] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "ink.document_evidence.v1",
            "source_id": self.source_id,
            "content_hash": self.content_hash,
            "metadata": self.metadata or {},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DocumentEvidence":
        return cls(**data)

@dataclass
class Attestation:
    attestation_id: str
    issuer: str
    content: str
    signature: str
    validity_period: dict[str, Any] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "ink.attestation.v1",
            "attestation_id": self.attestation_id,
            "issuer": self.issuer,
            "content": self.content,
            "signature": self.signature,
            "validity_period": self.validity_period or {},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Attestation":
        return cls(**data)

@dataclass
class ReviewerProfile:
    profile_id: str
    vertical: str
    required_evidence_classes: list[str] = None
    redaction_policy: str = "reviewer_minimum"
    gap_severity_threshold: str = "insufficient"
    section_ordering: list[str] = None
    required_disclaimers: list[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "ink.reviewer_profile.v1",
            "profile_id": self.profile_id,
            "vertical": self.vertical,
            "required_evidence_classes": self.required_evidence_classes or [],
            "redaction_policy": self.redaction_policy,
            "gap_severity_threshold": self.gap_severity_threshold,
            "section_ordering": self.section_ordering or [],
            "required_disclaimers": self.required_disclaimers or [],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewerProfile":
        return cls(**data)

@dataclass
class RedactionProfile:
    profile_id: str
    visibility_rules: dict[str, Any] = None
    output_format: str = "markdown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "ink.redaction_profile.v1",
            "profile_id": self.profile_id,
            "visibility_rules": self.visibility_rules or {},
            "output_format": self.output_format,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RedactionProfile":
        return cls(**data)

@dataclass
class RetentionProfile:
    profile_id: str
    storage_duration: str  # local_only, days_30, days_90, year_1, custom

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "ink.retention_profile.v1",
            "profile_id": self.profile_id,
            "storage_duration": self.storage_duration,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RetentionProfile":
        return cls(**data)