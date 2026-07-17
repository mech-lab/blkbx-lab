from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from blkbx_lab.evidence import EvidenceRecord, EvidenceRequirement, EvidenceGap


def normalize_risk_receipt(
    receipt: Dict[str, Any],
    action_id: str,
    model: str = "mand8",
    product: str = "mand8",
) -> EvidenceRecord:
    """
    Convert a MAND8 risk receipt to a normalized EvidenceRecord.
    
    Args:
        receipt: The MAND8 risk receipt dictionary
        action_id: Identifier for the action being recorded
        model: Model identifier used in the receipt
        product: Product identifier (default: mand8)
        
    Returns:
        EvidenceRecord: Normalized evidence record
    """
    # Extract information from the MAND8 risk receipt
    receipt_id = receipt.get("receipt_id", "")
    # Build evidence record from MAND8-specific fields
    evidence_record = EvidenceRecord(
        record_id=f"mand8_{receipt_id}_{int(datetime.now(timezone.utc).timestamp())}",
        product=product,
        action=action_id,
        model=model,
        input_commitments=_extract_mand8_input_commitments(receipt),
        output_commitments=_extract_mand8_output_commitments(receipt),
        policy_binding=_extract_mand8_policy_binding(receipt),
        control_evidence=_extract_mand8_control_evidence(receipt),
        evaluation_evidence=_extract_mand8_evaluation_evidence(receipt),
        exception_evidence=_extract_mand8_exception_evidence(receipt),
        incident_evidence=_extract_mand8_incident_evidence(receipt),
        human_authority=_extract_mand8_human_authority(receipt),
        disclosure_profile=_extract_mand8_disclosure_profile(receipt),
        integrity_provenance=_extract_mand8_integrity_provenance(receipt),
    )
    
    return evidence_record


def normalize_control_record(
    control_record: Dict[str, Any],
    action_id: str,
    model: str = "mand8",
    product: str = "mand8",
) -> EvidenceRecord:
    """
    Convert a MAND8 control record to a normalized EvidenceRecord.
    
    Args:
        control_record: The MAND8 control record dictionary
        action_id: Identifier for the action being recorded
        model: Model identifier used in the record
        product: Product identifier (default: mand8)
        
    Returns:
        EvidenceRecord: Normalized evidence record
    """
    evidence_record = EvidenceRecord(
        record_id=f"mand8_control_{action_id}_{int(datetime.now(timezone.utc).timestamp())}",
        product=product,
        action=action_id,
        model=model,
        input_commitments={},
        output_commitments={},
        policy_binding=_extract_mand8_policy_binding_from_control(control_record),
        control_evidence=_extract_mand8_control_evidence_from_control(control_record),
        evaluation_evidence=_extract_mand8_evaluation_evidence_from_control(control_record),
        exception_evidence=[],
        incident_evidence=[],
        human_authority={},
        disclosure_profile={},
        integrity_provenance={},
    )
    
    return evidence_record


def normalize_incident_record(
    incident_record: Dict[str, Any],
    action_id: str,
    model: str = "mand8",
    product: str = "mand8",
) -> EvidenceRecord:
    """
    Convert a MAND8 incident record to a normalized EvidenceRecord.
    
    Args:
        incident_record: The MAND8 incident record dictionary
        action_id: Identifier for the action being recorded
        model: Model identifier used in the record
        product: Product identifier (default: mand8)
        
    Returns:
        EvidenceRecord: Normalized evidence record
    """
    evidence_record = EvidenceRecord(
        record_id=f"mand8_incident_{action_id}_{int(datetime.now(timezone.utc).timestamp())}",
        product=product,
        action=action_id,
        model=model,
        input_commitments={},
        output_commitments={},
        policy_binding=_extract_mand8_policy_binding_from_incident(incident_record),
        control_evidence=[],
        evaluation_evidence=_extract_mand8_evaluation_evidence_from_incident(incident_record),
        exception_evidence=[],
        incident_evidence=_extract_mand8_incident_evidence_from_incident(incident_record),
        human_authority={},
        disclosure_profile={},
        integrity_provenance={},
    )
    
    return evidence_record


def normalize_override_record(
    override_record: Dict[str, Any],
    action_id: str,
    model: str = "mand8",
    product: str = "mand8",
) -> EvidenceRecord:
    """
    Convert a MAND8 override record to a normalized EvidenceRecord.
    
    Args:
        override_record: The MAND8 override record dictionary
        action_id: Identifier for the action being recorded
        model: Model identifier used in the record
        product: Product identifier (default: mand8)
        
    Returns:
        EvidenceRecord: Normalized evidence record
    """
    evidence_record = EvidenceRecord(
        record_id=f"mand8_override_{action_id}_{int(datetime.now(timezone.utc).timestamp())}",
        product=product,
        action=action_id,
        model=model,
        input_commitments={},
        output_commitments={},
        policy_binding=_extract_mand8_policy_binding_from_override(override_record),
        control_evidence=[],
        evaluation_evidence=_extract_mand8_evaluation_evidence_from_override(override_record),
        exception_evidence=[],
        incident_evidence=[],
        human_authority=_extract_mand8_human_authority_from_override(override_record),
        disclosure_profile={},
        integrity_provenance={},
    )
    
    return evidence_record


def normalize_bundle(
    bundle: Dict[str, Any],
    action_id: str,
    model: str = "mand8",
    product: str = "mand8",
) -> EvidenceRecord:
    """
    Convert a MAND8 bundle to a normalized EvidenceRecord.
    
    Args:
        bundle: The MAND8 bundle dictionary
        action_id: Identifier for the action being recorded
        model: Model identifier used in the bundle
        product: Product identifier (default: mand8)
        
    Returns:
        EvidenceRecord: Normalized evidence record
    """
    evidence_record = EvidenceRecord(
        record_id=f"mand8_bundle_{action_id}_{int(datetime.now(timezone.utc).timestamp())}",
        product=product,
        action=action_id,
        model=model,
        input_commitments={},
        output_commitments={},
        policy_binding=_extract_mand8_policy_binding_from_bundle(bundle),
        control_evidence=_extract_mand8_control_evidence_from_bundle(bundle),
        evaluation_evidence=_extract_mand8_evaluation_evidence_from_bundle(bundle),
        exception_evidence=[],
        incident_evidence=[],
        human_authority=_extract_mand8_human_authority_from_bundle(bundle),
        disclosure_profile=_extract_mand8_disclosure_profile_from_bundle(bundle),
        integrity_provenance=_extract_mand8_integrity_provenance_from_bundle(bundle),
    )
    
    return evidence_record


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
    Create an evidence requirement for MAND8 product.
    
    Args:
        requirement_id: Unique identifier for the requirement
        vertical: Business vertical (e.g., "insurance")
        artifact_type: Type of artifact (e.g., "ai_insurability_dossier")
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
    Create an evidence gap for MAND8 product.
    
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


def extract_evidence_from_bundle(
    bundle: Dict[str, Any],
) -> List[EvidenceRecord]:
    """
    Extract evidence records from a MAND8 bundle.
    
    Args:
        bundle: The MAND8 bundle dictionary
        
    Returns:
        List[EvidenceRecord]: List of extracted evidence records
    """
    evidence_records = []
    
    # Extract evidence from the receipt in the bundle
    receipt = bundle.get("receipt", {})
    if receipt:
        evidence_records.append(normalize_risk_receipt(receipt, "bundle_analysis"))
    
    # Extract evidence from control records if present
    # (MAND8 bundle structure may include control records)
    
    return evidence_records


def _extract_mand8_input_commitments(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """Extract input commitments from MAND8 risk receipt."""
    commitments = {}
    if "claim_root_hash" in receipt:
        commitments["claim_root_hash"] = receipt["claim_root_hash"]
    if "subject_hash" in receipt:
        commitments["subject_hash"] = receipt["subject_hash"]
    if "domain_context" in receipt:
        commitments["domain_context"] = receipt["domain_context"]
    return commitments


def _extract_mand8_output_commitments(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """Extract output commitments from MAND8 risk receipt."""
    commitments = {}
    if "commitments" in receipt:
        commitments.update(receipt["commitments"])
    return commitments


def _extract_mand8_policy_binding(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """Extract policy binding from MAND8 risk receipt."""
    policy_binding = {}
    if "policy" in receipt:
        policy_binding["policy_ref"] = receipt["policy"].get("ref")
        policy_binding["policy_hash"] = receipt["policy"].get("hash")
    if "commitments" in receipt and "policy_hash" in receipt["commitments"]:
        policy_binding["policy_hash"] = receipt["commitments"]["policy_hash"]
    return policy_binding


def _extract_mand8_control_evidence(receipt: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract control evidence from MAND8 risk receipt."""
    control_evidence = []
    if "control_evidence" in receipt:
        control_evidence.extend(receipt["control_evidence"])
    return control_evidence


def _extract_mand8_evaluation_evidence(receipt: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract evaluation evidence from MAND8 risk receipt."""
    evaluation_evidence = []
    if "evaluation_evidence" in receipt:
        evaluation_evidence.extend(receipt["evaluation_evidence"])
    return evaluation_evidence


def _extract_mand8_exception_evidence(receipt: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract exception evidence from MAND8 risk receipt."""
    exception_evidence = []
    if "exception_evidence" in receipt:
        exception_evidence.extend(receipt["exception_evidence"])
    return exception_evidence


def _extract_mand8_incident_evidence(receipt: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract incident evidence from MAND8 risk receipt."""
    incident_evidence = []
    if "incident_evidence" in receipt:
        incident_evidence.extend(receipt["incident_evidence"])
    return incident_evidence


def _extract_mand8_human_authority(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """Extract human authority from MAND8 risk receipt."""
    human_authority = {}
    if "human_authority" in receipt:
        human_authority.update(receipt["human_authority"])
    return human_authority


def _extract_mand8_disclosure_profile(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """Extract disclosure profile from MAND8 risk receipt."""
    disclosure_profile = {}
    if "disclosure_profile" in receipt:
        disclosure_profile.update(receipt["disclosure_profile"])
    return disclosure_profile


def _extract_mand8_integrity_provenance(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """Extract integrity provenance from MAND8 risk receipt."""
    integrity_provenance = {}
    if "integrity" in receipt:
        integrity_provenance.update(receipt["integrity"])
    if "signature" in receipt:
        integrity_provenance["signature"] = receipt["signature"]
    return integrity_provenance


def _extract_mand8_policy_binding_from_control(control_record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract policy binding from MAND8 control record."""
    return {
        "control_id": control_record.get("control_id"),
        "control_type": control_record.get("control_type"),
        "policy_ref": control_record.get("policy_ref"),
    }


def _extract_mand8_control_evidence_from_control(control_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract control evidence from MAND8 control record."""
    return [control_record]


def _extract_mand8_evaluation_evidence_from_control(control_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract evaluation evidence from MAND8 control record."""
    return []


def _extract_mand8_policy_binding_from_incident(incident_record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract policy binding from MAND8 incident record."""
    return {
        "incident_id": incident_record.get("incident_id"),
        "incident_type": incident_record.get("incident_type"),
        "policy_ref": incident_record.get("policy_ref"),
    }


def _extract_mand8_evaluation_evidence_from_incident(incident_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract evaluation evidence from MAND8 incident record."""
    return []


def _extract_mand8_incident_evidence_from_incident(incident_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract incident evidence from MAND8 incident record."""
    return [incident_record]


def _extract_mand8_policy_binding_from_override(override_record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract policy binding from MAND8 override record."""
    return {
        "override_id": override_record.get("override_id"),
        "override_type": override_record.get("override_type"),
        "policy_ref": override_record.get("policy_ref"),
    }


def _extract_mand8_evaluation_evidence_from_override(override_record: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract evaluation evidence from MAND8 override record."""
    return []


def _extract_mand8_human_authority_from_override(override_record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract human authority from MAND8 override record."""
    return {
        "override_id": override_record.get("override_id"),
        "override_type": override_record.get("override_type"),
        "human_review": override_record.get("human_review"),
    }


def _extract_mand8_policy_binding_from_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Extract policy binding from MAND8 bundle."""
    return {
        "bundle_id": bundle.get("bundle_id"),
        "bundle_type": bundle.get("bundle_type"),
        "audience": bundle.get("audience"),
    }


def _extract_mand8_control_evidence_from_bundle(bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract control evidence from MAND8 bundle."""
    return []


def _extract_mand8_evaluation_evidence_from_bundle(bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract evaluation evidence from MAND8 bundle."""
    return []


def _extract_mand8_human_authority_from_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Extract human authority from MAND8 bundle."""
    return {
        "bundle_id": bundle.get("bundle_id"),
        "audience": bundle.get("audience"),
    }


def _extract_mand8_disclosure_profile_from_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Extract disclosure profile from MAND8 bundle."""
    return {
        "bundle_id": bundle.get("bundle_id"),
        "audience": bundle.get("audience"),
    }


def _extract_mand8_integrity_provenance_from_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Extract integrity provenance from MAND8 bundle."""
    integrity_provenance = {}
    if "integrity" in bundle:
        integrity_provenance.update(bundle["integrity"])
    return integrity_provenance


__all__ = [
    "normalize_risk_receipt",
    "normalize_control_record",
    "normalize_incident_record",
    "normalize_override_record",
    "normalize_bundle",
    "create_evidence_requirement",
    "create_evidence_gap",
    "extract_evidence_from_bundle",
]
