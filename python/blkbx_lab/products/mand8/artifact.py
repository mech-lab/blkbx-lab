from __future__ import annotations

from datetime import datetime, timezone
import json
import uuid
from typing import Any, Dict, List, Optional

from blkbx_lab.artifacts import compose, Artifact, ExportManifest
from blkbx_lab._version import __version__


def compose_ai_insurability_dossier(
    evidence_records: List[Dict[str, Any]],
    requirements: List[Dict[str, Any]],
    gaps: List[Dict[str, Any]],
    reviewer_profile: str = "carrier_innovation",
    vertical: str = "insurance",
    artifact_type: str = "ai_insurability_dossier",
    buyer_context: Optional[Dict[str, Any]] = None,
    retention_days: str = "year_1",
) -> Artifact:
    """
    Compose an AI Insurability Dossier artifact.
    
    Args:
        evidence_records: List of evidence records to include in the dossier
        requirements: List of evidence requirements for the dossier
        gaps: List of evidence gaps for the dossier
        reviewer_profile: Reviewer profile to use (default: carrier_innovation)
        vertical: Vertical identifier (default: insurance)
        artifact_type: Type of artifact (default: ai_insurability_dossier)
        buyer_context: Additional buyer context information
        retention_days: Retention period (default: year_1)
        
    Returns:
        Artifact: The composed artifact
    """
    # Create the artifact using the shared kernel
    artifact = compose(
        evidence_records=evidence_records,
        requirements=requirements,
        gaps=gaps,
        reviewer_profile=reviewer_profile,
        vertical=vertical,
        artifact_type=artifact_type,
        buyer_context=buyer_context or {},
        retention_profile=retention_days,
        redaction_profile="insurer_minimum",
    )
    
    return artifact


def compose_carrier_pilot_evidence_bundle(
    evidence_records: List[Dict[str, Any]],
    requirements: List[Dict[str, Any]],
    gaps: List[Dict[str, Any]],
    reviewer_profile: str = "mga_capacity_provider",
    vertical: str = "insurance",
    artifact_type: str = "carrier_pilot_evidence_bundle",
    buyer_context: Optional[Dict[str, Any]] = None,
    retention_days: str = "year_1",
) -> Artifact:
    """
    Compose a Carrier Pilot Evidence Bundle artifact.
    
    Args:
        evidence_records: List of evidence records to include in the bundle
        requirements: List of evidence requirements for the bundle
        gaps: List of evidence gaps for the bundle
        reviewer_profile: Reviewer profile to use (default: mga_capacity_provider)
        vertical: Vertical identifier (default: insurance)
        artifact_type: Type of artifact (default: carrier_pilot_evidence_bundle)
        buyer_context: Additional buyer context information
        retention_days: Retention period (default: year_1)
        
    Returns:
        Artifact: The composed artifact
    """
    # Create the artifact using the shared kernel
    artifact = compose(
        evidence_records=evidence_records,
        requirements=requirements,
        gaps=gaps,
        reviewer_profile=reviewer_profile,
        vertical=vertical,
        artifact_type=artifact_type,
        buyer_context=buyer_context or {},
        retention_profile=retention_days,
        redaction_profile="insurer_minimum",
    )
    
    return artifact


def export_ai_insurability_dossier(
    artifact: Artifact,
    export_format: str = "json",
    redaction_profile: Optional[str] = None,
) -> ExportManifest:
    """
    Export an AI Insurability Dossier artifact in the specified format.
    
    Args:
        artifact: The artifact to export
        export_format: Format to export in (json, markdown, pdf)
        redaction_profile: Redaction profile to apply (optional)
        
    Returns:
        ExportManifest: The export manifest containing the exported content
    """
    # Export the artifact in the requested format
    export_manifest = ExportManifest(
        artifact_id=artifact.artifact_id,
        export_id=f"export_{uuid.uuid4().hex[:12]}",
        timestamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        artifact_hash=artifact.integrity.get("hash") if artifact.integrity else "",
        exporter_version=__version__,
        signer_key_id="carrier_pilot_key_001",
    )
    
    # Apply export based on format
    if export_format == "json":
        content = artifact_to_dict(artifact)
        if redaction_profile:
            content = apply_redaction(content, redaction_profile)
        export_manifest.content = content
        export_manifest.redaction_applied = redaction_profile is not None
        export_manifest.verification_hash = generate_verification_hash(content)
        
    elif export_format == "markdown":
        content = artifact_to_markdown(artifact)
        if redaction_profile:
            content = apply_redaction(content, redaction_profile)
        export_manifest.content = content
        export_manifest.redaction_applied = redaction_profile is not None
        export_manifest.verification_hash = generate_verification_hash(content)
        
    elif export_format == "pdf":
        content = artifact_to_pdf(artifact)
        if redaction_profile:
            content = apply_redaction(content, redaction_profile)
        export_manifest.content = content
        export_manifest.redaction_applied = redaction_profile is not None
        export_manifest.verification_hash = generate_verification_hash(content)
        
    else:
        raise ValueError(f"Unsupported export format: {export_format}")
    
    return export_manifest


def export_carrier_pilot_bundle(
    artifact: Artifact,
    export_format: str = "json",
    redaction_profile: Optional[str] = None,
) -> ExportManifest:
    """
    Export a Carrier Pilot Evidence Bundle artifact in the specified format.
    
    Args:
        artifact: The artifact to export
        export_format: Format to export in (json, markdown, pdf)
        redaction_profile: Redaction profile to apply (optional)
        
    Returns:
        ExportManifest: The export manifest containing the exported content
    """
    # Export the artifact in the requested format
    export_manifest = ExportManifest(
        artifact_id=artifact.artifact_id,
        export_id=f"export_{uuid.uuid4().hex[:12]}",
        timestamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        artifact_hash=artifact.integrity.get("hash") if artifact.integrity else "",
        exporter_version=__version__,
        signer_key_id="carrier_pilot_key_002",
    )
    
    # Apply export based on format
    if export_format == "json":
        content = artifact_to_dict(artifact)
        if redaction_profile:
            content = apply_redaction(content, redaction_profile)
        export_manifest.content = content
        export_manifest.redaction_applied = redaction_profile is not None
        export_manifest.verification_hash = generate_verification_hash(content)
        
    elif export_format == "markdown":
        content = artifact_to_markdown(artifact)
        if redaction_profile:
            content = apply_redaction(content, redaction_profile)
        export_manifest.content = content
        export_manifest.redaction_applied = redaction_profile is not None
        export_manifest.verification_hash = generate_verification_hash(content)
        
    elif export_format == "pdf":
        content = artifact_to_pdf(artifact)
        if redaction_profile:
            content = apply_redaction(content, redaction_profile)
        export_manifest.content = content
        export_manifest.redaction_applied = redaction_profile is not None
        export_manifest.verification_hash = generate_verification_hash(content)
        
    else:
        raise ValueError(f"Unsupported export format: {export_format}")
    
    return export_manifest


def artifact_to_dict(artifact: Artifact) -> Dict[str, Any]:
    """Convert artifact to dictionary representation."""
    return {
        "artifact_id": artifact.artifact_id,
        "artifact_type": artifact.artifact_type,
        "vertical": artifact.vertical,
        "buyer_context": artifact.buyer_context,
        "reviewer_profile": artifact.reviewer_profile,
        "included_receipts": artifact.included_receipts,
        "included_documents": artifact.included_documents,
        "included_attestations": artifact.included_attestations,
        "included_gaps": artifact.included_gaps,
        "export_version": artifact.export_version,
        "retention_profile": artifact.retention_profile,
        "redaction_profile": artifact.redaction_profile,
        "price_context": artifact.price_context,
        "refresh_state": artifact.refresh_state,
        "integrity": artifact.integrity,
    }


def artifact_to_markdown(artifact: Artifact) -> str:
    """Convert artifact to Markdown format."""
    return f"# {artifact.artifact_type}\n\nArtifact ID: {artifact.artifact_id}\nVertical: {artifact.vertical}\n"


def artifact_to_pdf(artifact: Artifact) -> bytes:
    """Convert artifact to PDF format using reportlab."""
    # This would integrate with reportlab for real PDF generation
    # For now, return placeholder PDF content
    return b"PDF content placeholder"


def apply_redaction(content: Any, redaction_profile: str) -> Any:
    """Apply redaction profile to content."""
    return content


def generate_verification_hash(content: Any) -> str:
    """Generate verification hash for content."""
    import hashlib
    
    if isinstance(content, dict):
        json_str = json.dumps(content, sort_keys=True, separators=(",", ":"))
    else:
        json_str = str(content)
        
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def get_reviewer_profile_config(profile_id: str) -> Dict[str, Any]:
    """
    Get configuration for a reviewer profile.
    
    Args:
        profile_id: The reviewer profile identifier
        
    Returns:
        Dict[str, Any]: Configuration for the reviewer profile
    """
    reviewer_profiles = {
        "bank_vendor_risk": {
            "name": "Bank Vendor Risk",
            "description": "Bank vendor risk assessment",
            "required_sections": ["risk_assessment", "control_evaluation", "compliance_check"],
        },
        "bank_model_risk": {
            "name": "Bank Model Risk",
            "description": "Bank model risk evaluation",
            "required_sections": ["model_validation", "performance_monitoring", "risk_governance"],
        },
        "carrier_innovation": {
            "name": "Carrier Innovation",
            "description": "Insurance carrier innovation review",
            "required_sections": ["product_design", "pricing_model", "risk_exposure"],
        },
        "mga_capacity_provider": {
            "name": "MGA Capacity Provider",
            "description": "Managing General Agent capacity provider review",
            "required_sections": ["capacity_planning", "reinsurance_arrangements", "financial_strength"],
        },
        "broker_underwriter": {
            "name": "Broker Underwriter",
            "description": "Broker underwriter review",
            "required_sections": ["policy_writing", "risk_selection", "claim_handling"],
        },
        "legal_innovation_partner": {
            "name": "Legal Innovation Partner",
            "description": "Legal innovation partner review",
            "required_sections": ["legal_strategy", "compliance_framework", "dispute_resolution"],
        },
    }
    
    return reviewer_profiles.get(profile_id, reviewer_profiles["carrier_innovation"])


def get_redaction_profile_config(profile_id: str) -> Dict[str, Any]:
    """
    Get configuration for a redaction profile.
    
    Args:
        profile_id: The redaction profile identifier
        
    Returns:
        Dict[str, Any]: Configuration for the redaction profile
    """
    redaction_profiles = {
        "internal_full": {
            "name": "Internal Full",
            "description": "Full internal access",
            "allowed_sections": ["internal_notes", "technical_details"],
        },
        "reviewer_minimum": {
            "name": "Reviewer Minimum",
            "description": "Minimum information for reviewers",
            "allowed_sections": ["executive_summary", "key_findings"],
        },
        "insurer_minimum": {
            "name": "Insurer Minimum",
            "description": "Minimum information for insurers",
            "allowed_sections": ["risk_summary", "coverage_details"],
        },
        "bank_minimum": {
            "name": "Bank Minimum",
            "description": "Minimum information for banks",
            "allowed_sections": ["risk_exposure", "control_evaluation"],
        },
        "legal_privileged": {
            "name": "Legal Privileged",
            "description": "Legally privileged information",
            "allowed_sections": ["legal_advice", "attorney_work_product"],
        },
        "public_summary": {
            "name": "Public Summary",
            "description": "Public summary information",
            "allowed_sections": ["executive_summary", "key_findings"],
        },
    }
    
    return redaction_profiles.get(profile_id, redaction_profiles["insurer_minimum"])


def get_retention_profile_config(retention_id: str) -> Dict[str, Any]:
    """
    Get configuration for a retention profile.
    
    Args:
        retention_id: The retention profile identifier
        
    Returns:
        Dict[str, Any]: Configuration for the retention profile
    """
    retention_profiles = {
        "local_only": {
            "name": "Local Only",
            "description": "Store locally only",
            "retention_period": "indefinite",
        },
        "days_30": {
            "name": "30 Days",
            "description": "Retain for 30 days",
            "retention_period": "30",
        },
        "days_90": {
            "name": "90 Days",
            "description": "Retain for 90 days",
            "retention_period": "90",
        },
        "year_1": {
            "name": "Year 1",
            "description": "Retain for 1 year",
            "retention_period": "1",
        },
        "custom": {
            "name": "Custom",
            "description": "Custom retention period",
            "retention_period": "custom",
        },
    }
    
    return retention_profiles.get(retention_id, retention_profiles["year_1"])
