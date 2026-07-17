"""MAND8 delegated-authority receipts."""

from __future__ import annotations

from typing import Any

from .receipt import (
    _event,
    _issued_at,
    _normalized_human_review,
    _stub_integrity,
    refresh_integrity,
    with_human_review,
)

SCHEMA_ID = "mand8.authority_receipt.v1"


def as_event_payload(authority_receipt: dict[str, Any]) -> dict[str, Any]:
    if authority_receipt.get("schema") != SCHEMA_ID:
        payload = dict(authority_receipt)
        case_id = payload.get("case_id") or payload.get("domain_context", {}).get("case_id")
        if case_id is not None:
            payload.setdefault("case_id", case_id)
        return payload

    scope = authority_receipt.get("authority_scope", {})
    context = authority_receipt.get("domain_context", {})
    return {
        "schema": authority_receipt.get("schema"),
        "receipt_id": authority_receipt.get("receipt_id"),
        "case_id": authority_receipt.get("case_id"),
        "authority_id": scope.get("authority_id"),
        "construct": scope.get("construct"),
        "status": scope.get("status"),
        "lloyds_binding_ref": context.get("lloyds_binding_ref") or context.get("binder_ref"),
        "managing_agent": context.get("managing_agent"),
        "coverholder": context.get("coverholder"),
    }


def record(
    *,
    policy_ref: str,
    binder_ref: str,
    authority_id: str,
    lloyds_binding_ref: str | None = None,
    managing_agent: str | None = None,
    coverholder: str | None = None,
    permitted_risk_classes: list[str] | None = None,
    controls_required: list[str] | None = None,
    policy_conditions: list[str] | None = None,
    exclusions: list[str] | None = None,
    regulators: list[str] | None = None,
    territory: str = "UK",
    market_segment: str = "lloyds_delegated_authority",
    construct: str = "delegated_authority",
    status: str = "within_authority",
    delegated_authority: bool = True,
    authority_notes: str | None = None,
    human_review: dict[str, Any] | None = None,
    case_id: str | None = None,
    receipt_id: str | None = None,
    action_id: str | None = None,
) -> dict[str, Any]:
    import uuid

    resolved_case_id = case_id or f"case_{uuid.uuid4().hex[:12]}"
    body = {
        "schema": SCHEMA_ID,
        "receipt_id": receipt_id or f"arcpt_{uuid.uuid4().hex[:12]}",
        "action_id": action_id or f"act_{uuid.uuid4().hex[:12]}",
        "case_id": resolved_case_id,
        "issued_at": _issued_at(),
        "domain_context": {
            "case_id": resolved_case_id,
            "policy_ref": policy_ref,
            "binder_ref": binder_ref,
            "lloyds_binding_ref": lloyds_binding_ref or binder_ref,
            "territory": territory,
            "market_segment": market_segment,
            "managing_agent": managing_agent,
            "coverholder": coverholder,
            "regulators": regulators or (["FCA", "PRA"] if territory == "UK" else []),
        },
        "authority_scope": {
            "authority_id": authority_id,
            "construct": construct,
            "status": status,
            "delegated_authority": delegated_authority,
            "permitted_risk_classes": permitted_risk_classes or [],
            "controls_required": controls_required or [],
            "policy_conditions": policy_conditions or [],
            "exclusions": exclusions or [],
            "authority_notes": authority_notes,
        },
        "event_trail": [
            _event(
                "delegated_authority_checked",
                {
                    "case_id": resolved_case_id,
                    "authority_id": authority_id,
                    "status": status,
                    "lloyds_binding_ref": lloyds_binding_ref or binder_ref,
                },
            )
        ],
        "human_review": _normalized_human_review(None),
    }
    authority_receipt = dict(body)
    authority_receipt["integrity"] = _stub_integrity(body)
    return with_human_review(authority_receipt, human_review)
