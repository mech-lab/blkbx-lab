from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from blkbx_lab.artifacts import ArtifactExport
from blkbx_lab.evidence import EvidenceGap, EvidenceRecord, EvidenceRequirement
from blkbx_lab.results import (
    ActionEvidenceBundle,
    DoctorResult,
    GateAnalysisResult,
    InkReceiptResult,
)


def normalize_trace_result(
    trace_result: InkReceiptResult,
    action_id: str,
    model: str = "unknown",
    product: str = "blkbxs",
) -> EvidenceRecord:
    """
    Convert a trace result (InkReceiptResult) to a normalized EvidenceRecord.
    
    Args:
        trace_result: The result from blkbx_lab.trace()
        action_id: Identifier for the action being traced
        model: Model identifier used in the trace
        product: Product identifier (default: blkbxs)
        
    Returns:
        EvidenceRecord: Normalized evidence record
    """
    # Extract information from the trace result
    receipt_path = trace_result.receipt_path
    summary = trace_result.summary
    verification = trace_result.verification
    
    # Load the receipt to extract detailed information
    receipt_data = {}
    if receipt_path and Path(receipt_path).exists():
        receipt_data = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
    
    # Build evidence record
    evidence_record = EvidenceRecord(
        record_id=f"trace_{action_id}_{int(datetime.now(timezone.utc).timestamp())}",
        product=product,
        action=action_id,
        model=model,
        input_commitments=_extract_input_commitments(receipt_data),
        output_commitments=_extract_output_commitments(receipt_data),
        policy_binding=_extract_policy_binding(receipt_data),
        control_evidence=_extract_control_evidence(receipt_data),
        evaluation_evidence=_extract_evaluation_evidence(receipt_data, summary),
        exception_evidence=_extract_exception_evidence(receipt_data),
        incident_evidence=_extract_incident_evidence(receipt_data),
        human_authority=_extract_human_authority(receipt_data),
        disclosure_profile=_extract_disclosure_profile(receipt_data),
        integrity_provenance=_extract_integrity_provenance(receipt_data, verification),
    )
    
    return evidence_record


def normalize_gate_result(
    gate_result: GateAnalysisResult,
    action_id: str,
    model: str = "unknown",
    product: str = "blkbxs",
) -> EvidenceRecord:
    """
    Convert a gate analysis result to a normalized EvidenceRecord.
    
    Args:
        gate_result: The result from blkbx_lab.gate()
        action_id: Identifier for the action being gated
        model: Model identifier used in the analysis
        product: Product identifier (default: blkbxs)
        
    Returns:
        EvidenceRecord: Normalized evidence record
    """
    evidence_record = EvidenceRecord(
        record_id=f"gate_{action_id}_{int(datetime.now(timezone.utc).timestamp())}",
        product=product,
        action=action_id,
        model=model,
        input_commitments={},
        output_commitments={},
        policy_binding=_extract_policy_binding_from_gate(gate_result),
        control_evidence=_extract_control_evidence_from_gate(gate_result),
        evaluation_evidence=_extract_evaluation_evidence_from_gate(gate_result),
        exception_evidence=[],
        incident_evidence=[],
        human_authority={},
        disclosure_profile={},
        integrity_provenance={},
    )
    
    return evidence_record


def normalize_doctor_result(
    doctor_result: DoctorResult,
    action_id: str = "system_health",
    model: str = "unknown",
    product: str = "blkbxs",
) -> EvidenceRecord:
    """
    Convert a doctor result to a normalized EvidenceRecord.
    
    Args:
        doctor_result: The result from blkbx_lab.doctor()
        action_id: Identifier for the health check action
        model: Model identifier used in the check
        product: Product identifier (default: blkbxs)
        
    Returns:
        EvidenceRecord: Normalized evidence record
    """
    evidence_record = EvidenceRecord(
        record_id=f"doctor_{action_id}_{int(datetime.now(timezone.utc).timestamp())}",
        product=product,
        action=action_id,
        model=model,
        input_commitments={},
        output_commitments={},
        policy_binding={},
        control_evidence=doctor_result.checks,
        evaluation_evidence=[],
        exception_evidence=[],
        incident_evidence=[],
        human_authority={},
        disclosure_profile={},
        integrity_provenance={"status": doctor_result.status},
    )
    
    return evidence_record


def normalize_action_evidence_bundle(
    bundle: ActionEvidenceBundle,
    action_id: str,
    model: str = "unknown",
    product: str = "blkbxs",
) -> EvidenceRecord:
    """
    Convert an action evidence bundle to a normalized EvidenceRecord.
    
    Args:
        bundle: The action evidence bundle
        action_id: Identifier for the action
        model: Model identifier used
        product: Product identifier (default: blkbxs)
        
    Returns:
        EvidenceRecord: Normalized evidence record
    """
    evidence_record = EvidenceRecord(
        record_id=f"bundle_{action_id}_{int(datetime.now(timezone.utc).timestamp())}",
        product=product,
        action=action_id,
        model=model,
        input_commitments={},
        output_commitments={},
        policy_binding={},
        control_evidence=[],
        evaluation_evidence=[],
        exception_evidence=[],
        incident_evidence=[],
        human_authority={},
        disclosure_profile={},
        integrity_provenance={},
    )
    
    return evidence_record


def _extract_input_commitments(receipt_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract input commitments from receipt data."""
    commitments = {}
    if "claim_root_hash" in receipt_data:
        commitments["claim_root_hash"] = receipt_data["claim_root_hash"]
    if "subject_hash" in receipt_data:
        commitments["subject_hash"] = receipt_data["subject_hash"]
    return commitments


def _extract_output_commitments(receipt_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract output commitments from receipt data."""
    commitments = {}
    receipt_commitments = receipt_data.get("commitments", {})
    if "evidence_root_hash" in receipt_data:
        commitments["evidence_root_hash"] = receipt_data["evidence_root_hash"]
    if "policy_hash" in receipt_commitments:
        commitments["policy_hash"] = receipt_commitments["policy_hash"]
    return commitments


def _extract_policy_binding(receipt_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract policy binding from receipt data."""
    policy_binding = {}
    if "policy" in receipt_data:
        policy_binding["policy_ref"] = receipt_data["policy"].get("ref")
        policy_binding["policy_hash"] = receipt_data["policy"].get("hash")
    if "commitments" in receipt_data and "policy_hash" in receipt_data["commitments"]:
        policy_binding["policy_hash"] = receipt_data["commitments"]["policy_hash"]
    return policy_binding


def _extract_policy_binding_from_gate(gate_result: GateAnalysisResult) -> Dict[str, Any]:
    """Extract policy binding from gate result."""
    return {
        "risk_tier": gate_result.risk_tier,
        "required_controls": gate_result.required_controls,
        "missing_controls": gate_result.missing_controls,
        "recommended_decision": gate_result.recommended_decision,
    }


def _extract_control_evidence(receipt_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract control evidence from receipt data."""
    control_evidence = []
    if "control_evidence" in receipt_data:
        control_evidence.extend(receipt_data["control_evidence"])
    return control_evidence


def _extract_control_evidence_from_gate(gate_result: GateAnalysisResult) -> List[Dict[str, Any]]:
    """Extract control evidence from gate result."""
    control_evidence = []
    for control in gate_result.required_controls:
        control_evidence.append({
            "control_id": control,
            "status": "required",
            "evidence_source": "gate_analysis"
        })
    for control in gate_result.missing_controls:
        control_evidence.append({
            "control_id": control,
            "status": "missing",
            "evidence_source": "gate_analysis"
        })
    return control_evidence


def _extract_evaluation_evidence(receipt_data: Dict[str, Any], summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract evaluation evidence from receipt data and summary."""
    evaluation_evidence = []
    if "evaluation_evidence" in receipt_data:
        evaluation_evidence.extend(receipt_data["evaluation_evidence"])
    if summary:
        evaluation_evidence.append({
            "evaluation_summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    return evaluation_evidence


def _extract_evaluation_evidence_from_gate(gate_result: GateAnalysisResult) -> List[Dict[str, Any]]:
    """Extract evaluation evidence from gate result."""
    evaluation_evidence = []
    evaluation_evidence.append({
        "gate_analysis": {
            "risk_tier": gate_result.risk_tier,
            "required_controls": gate_result.required_controls,
            "missing_controls": gate_result.missing_controls,
            "recommended_decision": gate_result.recommended_decision,
            "summary": gate_result.summary,
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    return evaluation_evidence


def _extract_exception_evidence(receipt_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract exception evidence from receipt data."""
    exception_evidence = []
    if "exception_evidence" in receipt_data:
        exception_evidence.extend(receipt_data["exception_evidence"])
    return exception_evidence


def _extract_incident_evidence(receipt_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract incident evidence from receipt data."""
    incident_evidence = []
    if "incident_evidence" in receipt_data:
        incident_evidence.extend(receipt_data["incident_evidence"])
    return incident_evidence


def _extract_human_authority(receipt_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract human authority from receipt data."""
    human_authority = {}
    if "human_authority" in receipt_data:
        human_authority.update(receipt_data["human_authority"])
    return human_authority


def _extract_disclosure_profile(receipt_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract disclosure profile from receipt data."""
    disclosure_profile = {}
    if "disclosure_profile" in receipt_data:
        disclosure_profile.update(receipt_data["disclosure_profile"])
    return disclosure_profile


def _extract_integrity_provenance(
    receipt_data: Dict[str, Any], 
    verification: Dict[str, Any]
) -> Dict[str, Any]:
    """Extract integrity provenance from receipt data and verification."""
    integrity_provenance = {}
    if "integrity" in receipt_data:
        integrity_provenance.update(receipt_data["integrity"])
    if verification:
        integrity_provenance["verification"] = verification
    if "signature" in receipt_data:
        integrity_provenance["signature"] = receipt_data["signature"]
    return integrity_provenance


def create_evidence_requirement(
    requirement_id: str,
    vertical: str,
    artifact_type: str,
    support_type: str,
    coverage_status: str,
    reviewer_profiles: Optional[List[str]] = None,
    mapped_receipts: Optional[List[str]] = None,
    mapped_documents: Optional[List[str]] = None,
    mapped_attestations: Optional[List[str]] = None,
    notes: str = "",
) -> EvidenceRequirement:
    """
    Create an evidence requirement for BLKBXS product.
    
    Args:
        requirement_id: Unique identifier for the requirement
        vertical: Business vertical (e.g., "banking")
        artifact_type: Type of artifact (e.g., "bank_pilot_evidence_bundle")
        support_type: Type of support needed (machine_verifiable, document_verifiable, attestation_required)
        coverage_status: Current coverage status (covered, missing, stale, insufficient, reviewer_specific)
        reviewer_profiles: List of reviewer profiles that care about this requirement
        mapped_receipts: List of receipt IDs that map to this requirement
        mapped_documents: List of document hashes that map to this requirement
        mapped_attestations: List of attestation IDs that map to this requirement
        notes: Additional notes about the requirement
        
    Returns:
        EvidenceRequirement: The created evidence requirement
    """
    return EvidenceRequirement(
        requirement_id=requirement_id,
        vertical=vertical,
        artifact_type=artifact_type,
        support_type=support_type,
        coverage_status=coverage_status,
        reviewer_profiles=reviewer_profiles or [],
        mapped_receipts=mapped_receipts or [],
        mapped_documents=mapped_documents or [],
        mapped_attestations=mapped_attestations or [],
        notes=notes,
    )


def create_evidence_gap(
    gap_id: str,
    requirement_id: str,
    gap_type: str,
    severity: str,
    reviewer_importance: str,
    remediation_path: str,
    estimated_effort: str,
    bundle_blocking: bool,
    notes: str = "",
) -> EvidenceGap:
    """
    Create an evidence gap for BLKBXS product.
    
    Args:
        gap_id: Unique identifier for the gap
        requirement_id: ID of the requirement this gap relates to
        gap_type: Type of gap (machine_verifiable, document_verifiable, attestation_required)
        severity: Severity level (low, medium, high, critical)
        reviewer_importance: Importance to reviewer (low, medium, high, critical)
        remediation_path: How to fix the gap
        estimated_effort: Estimated effort to fix (low, medium, high)
        bundle_blocking: Whether this gap blocks bundle creation
        notes: Additional notes about the gap
        
    Returns:
        EvidenceGap: The created evidence gap
    """
    return EvidenceGap(
        gap_id=gap_id,
        requirement_id=requirement_id,
        gap_type=gap_type,
        severity=severity,
        reviewer_importance=reviewer_importance,
        remediation_path=remediation_path,
        estimated_effort=estimated_effort,
        bundle_blocking=bundle_blocking,
        notes=notes,
    )


def extract_evidence_from_artifact_export(
    artifact_export: ArtifactExport,
) -> List[EvidenceRecord]:
    """
    Extract evidence records from an artifact export.
    
    Args:
        artifact_export: The artifact export to extract evidence from
        
    Returns:
        List[EvidenceRecord]: List of extracted evidence records
    """
    # This would extract evidence from the artifact export content
    # For now, return an empty list as a placeholder
    return []


__all__ = [
    "normalize_trace_result",
    "normalize_gate_result",
    "normalize_doctor_result",
    "normalize_action_evidence_bundle",
    "create_evidence_requirement",
    "create_evidence_gap",
    "extract_evidence_from_artifact_export",
]
