"""MAND8 bundle export."""

from __future__ import annotations

from importlib.resources import files
import uuid
from typing import Any

from .._common import issued_at, stub_integrity
from .receipt import case_identifier

BUNDLE_SCHEMA_ID = "mand8.bundle.v1"
INSTITUTIONAL_QUESTION = "Can this AI risk be priced, underwritten, monitored, renewed, and defended?"


def available_templates() -> list[str]:
    return sorted(path.name for path in files("mand8.bundles").iterdir() if path.name.endswith(".md"))


def load_template(template_name: str) -> str:
    return files("mand8.bundles").joinpath(template_name).read_text(encoding="utf-8")


def _event_payloads(receipt: dict[str, Any], event_type: str) -> list[dict[str, Any]]:
    return [
        dict(entry.get("payload", {}))
        for entry in receipt.get("event_trail", [])
        if entry.get("event_type") == event_type
    ]


def _event_count(receipt: dict[str, Any], event_type: str) -> int:
    return sum(1 for entry in receipt.get("event_trail", []) if entry.get("event_type") == event_type)


def _coverage_summary(
    receipt: dict[str, Any],
    authority_receipts: list[dict[str, Any]],
    incident_receipts: list[dict[str, Any]],
    verification_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    review_status = receipt.get("human_review", {}).get("status", "not_reviewed")
    override_count = _event_count(receipt, "override_recorded")
    control_count = _event_count(receipt, "control_check_recorded")
    return {
        "risk_receipt_id": receipt.get("receipt_id"),
        "authority_receipt_count": len(authority_receipts),
        "incident_receipt_count": len(incident_receipts),
        "control_check_count": control_count,
        "override_count": override_count,
        "human_review_status": review_status,
        "latest_authority_status": next(
            (
                item.get("authority_scope", {}).get("status") or item.get("status")
                for item in reversed(authority_receipts)
                if isinstance(item, dict)
            ),
            receipt.get("domain_context", {}).get("authority_status"),
        ),
        "latest_incident_severity": next(
            (item.get("severity") for item in reversed(incident_receipts) if isinstance(item, dict)),
            receipt.get("domain_context", {}).get("last_incident_severity"),
        ),
        "verification_statuses": [item.get("status", "unknown") for item in verification_reports],
        "renewal_ready": review_status == "reviewed" and control_count > 0 and not incident_receipts,
    }


def export(
    receipt: dict[str, Any],
    bundle_type: str = "underwriting_evidence_bundle",
    audience: str = "lloyds_underwriter",
    notes: str | None = None,
    bundle_sections: list[str] | None = None,
    authority_receipts: list[dict[str, Any]] | None = None,
    incident_receipts: list[dict[str, Any]] | None = None,
    verification_reports: list[dict[str, Any]] | None = None,
    related_receipts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    case_id = case_identifier(receipt)
    authority_items = authority_receipts or _event_payloads(receipt, "authority_receipt_recorded")
    incident_items = incident_receipts or _event_payloads(receipt, "incident_recorded")
    verification_items = list(verification_reports or [])
    sections = bundle_sections or [
        "Authority Receipt",
        "Exposure Unit",
        "Risk Controls",
        "Override State",
        "Human Review",
        "Incident Review",
        "Verification Reports",
    ]
    related = {
        "risk_receipt_id": receipt.get("receipt_id"),
        "authority_receipt_ids": [
            item.get("receipt_id") or item.get("authority_id")
            for item in authority_items
            if isinstance(item, dict)
        ],
        "incident_receipt_ids": [
            item.get("receipt_id") or item.get("incident_id")
            for item in incident_items
            if isinstance(item, dict)
        ],
    }
    if related_receipts:
        related.update(related_receipts)
    body = {
        "schema": BUNDLE_SCHEMA_ID,
        "bundle_id": f"bundle_{uuid.uuid4().hex[:12]}",
        "case_id": case_id,
        "bundle_type": bundle_type,
        "audience": audience,
        "generated_at": issued_at(),
        "institutional_question": INSTITUTIONAL_QUESTION,
        "market_context": {
            "territory": receipt.get("domain_context", {}).get("territory"),
            "market_segment": receipt.get("domain_context", {}).get("market_segment"),
            "binder_ref": receipt.get("domain_context", {}).get("binder_ref"),
            "managing_agent": receipt.get("domain_context", {}).get("managing_agent"),
        },
        "bundle_sections": sections,
        "notes": notes,
        "receipt": receipt,
        "authority_receipts": authority_items,
        "incident_receipts": incident_items,
        "related_receipts": related,
        "coverage_summary": _coverage_summary(receipt, authority_items, incident_items, verification_items),
        "verification_reports": verification_items,
        "summary": (
            f"{bundle_type} for {audience}: "
            f"{receipt.get('domain_context', {}).get('policy_ref', 'unknown policy')} "
            f"with {len(receipt.get('event_trail', []))} receipt events, "
            f"{len(authority_items)} authority receipts, and {len(incident_items)} incident receipts"
        ),
    }
    bundle = dict(body)
    bundle["integrity"] = stub_integrity(body)
    return bundle


def summarize(bundle: dict[str, Any]) -> str:
    return str(bundle.get("summary", "MAND8 bundle"))


__all__ = [
    "BUNDLE_SCHEMA_ID",
    "INSTITUTIONAL_QUESTION",
    "available_templates",
    "export",
    "load_template",
    "summarize",
]
