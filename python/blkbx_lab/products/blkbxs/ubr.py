"""Universal Banking Receipt helpers for BLKBXS."""

from __future__ import annotations

from typing import Any

from .._common import issued_at, new_identifier
from .graph import validate_graph

SCHEMA_ID = "blkbxs.ubr.receipt.v1"


def create_event(
    operation_name: str,
    business_process_id: str,
    receipt_id: str | None = None,
    profile: list[str] | None = None,
    issued_at_value: str | None = None,
    operation: dict[str, Any] | None = None,
    parties: list[dict[str, Any]] | None = None,
    authority: dict[str, Any] | None = None,
    state_transition: dict[str, Any] | None = None,
    evidence: list[dict[str, Any]] | None = None,
    compliance: dict[str, Any] | None = None,
    links: dict[str, Any] | None = None,
    ai_assistance: dict[str, Any] | None = None,
    verification: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_id = receipt_id or f"urn:ubr:{new_identifier('event')}"
    resolved_issued_at = issued_at_value or issued_at()
    resolved_operation = {
        "domain": "loan",
        "name": operation_name,
        "phase": "event",
        "action": "recorded",
        "status": "completed",
        "business_process_id": business_process_id,
    }
    if operation:
        resolved_operation.update(operation)
        resolved_operation["name"] = operation_name
        resolved_operation["business_process_id"] = business_process_id

    return {
        "id": resolved_id,
        "type": "UniversalBankingReceipt",
        "version": "0.1.0",
        "profile": profile or ["ubr.core.v0"],
        "issued_at": resolved_issued_at,
        "jurisdiction": ["US"],
        "language": "en-US",
        "operation": resolved_operation,
        "parties": parties or [{"role": "issuer", "type": "financial_institution", "id": "did:web:example-bank.test"}],
        "authority": authority or {},
        "state_transition": state_transition or {"subject": {"type": "event", "id": resolved_id}, "before": {}, "after": {}},
        "evidence": evidence or [],
        "compliance": compliance or {},
        "links": {
            "bundle_id": f"urn:ubr-bundle:{business_process_id}",
            "parent_receipts": [],
            **(links or {}),
        },
        "ai_assistance": ai_assistance or {"used": False, "systems": [], "risk_controls": {}},
        "verification": verification or {
            "canonicalization": "demo-jcs-compatible-json-sort-keys",
            "digest_alg": "SHA-256",
            "signature_alg": "Ed25519",
            "verification_method": "demo-only",
            "status": {"state": "active", "status_purpose": "revocation"},
            "timestamp": {"method": "issued_at_demo", "value": resolved_issued_at},
            "digest": "sha256:" + "0" * 64,
            "proofs": [],
        },
    }


__all__ = ["SCHEMA_ID", "create_event", "validate_graph"]
