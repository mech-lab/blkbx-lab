"""MAND8 bundle export."""

from __future__ import annotations

import uuid
from typing import Any

from .receipt import _issued_at, _stub_integrity

BUNDLE_SCHEMA_ID = "mand8.bundle.v1"
INSTITUTIONAL_QUESTION = "Can this AI risk be priced, underwritten, monitored, renewed, and defended?"


def export(
    receipt: dict[str, Any],
    bundle_type: str = "underwriting_evidence_bundle",
    audience: str = "lloyds_underwriter",
    notes: str | None = None,
    bundle_sections: list[str] | None = None,
) -> dict[str, Any]:
    sections = bundle_sections or [
        "Authority Receipt",
        "Exposure Unit",
        "Risk Controls",
        "Override State",
        "Human Review",
    ]
    body = {
        "schema": BUNDLE_SCHEMA_ID,
        "bundle_id": f"bundle_{uuid.uuid4().hex[:12]}",
        "bundle_type": bundle_type,
        "audience": audience,
        "generated_at": _issued_at(),
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
        "summary": (
            f"{bundle_type} for {audience}: "
            f"{receipt.get('domain_context', {}).get('policy_ref', 'unknown policy')} "
            f"with {len(receipt.get('event_trail', []))} receipt events"
        ),
    }
    bundle = dict(body)
    bundle["integrity"] = _stub_integrity(body)
    return bundle


def summarize(bundle: dict[str, Any]) -> str:
    return str(bundle.get("summary", "MAND8 bundle"))
