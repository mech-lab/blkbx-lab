"""DUE bundle export."""

from __future__ import annotations

import uuid
from typing import Any

from .receipt import _issued_at, _stub_integrity

BUNDLE_SCHEMA_ID = "due.dispute_bundle.v1"
INSTITUTIONAL_QUESTION = "Can this AI-assisted action survive challenge, dispute, discovery, privilege review, disclosure review, and liability scrutiny?"


def export(
    receipt: dict[str, Any],
    bundle_type: str = "legal_defensibility_bundle",
    audience: str = "counsel",
    notes: str | None = None,
    bundle_sections: list[str] | None = None,
) -> dict[str, Any]:
    sections = bundle_sections or [
        "Matter Context",
        "Authority",
        "Privilege",
        "Disclosure",
        "Human Review",
        "Chain of Custody",
    ]
    body = {
        "schema": BUNDLE_SCHEMA_ID,
        "bundle_id": f"bundle_{uuid.uuid4().hex[:12]}",
        "bundle_type": bundle_type,
        "audience": audience,
        "generated_at": _issued_at(),
        "institutional_question": INSTITUTIONAL_QUESTION,
        "bundle_sections": sections,
        "notes": notes,
        "receipt": receipt,
        "summary": (
            f"{bundle_type} for {audience}: "
            f"{receipt.get('domain_context', {}).get('matter_id', 'unbound matter')} "
            f"with {len(receipt.get('event_trail', []))} receipt events"
        ),
    }
    bundle = dict(body)
    bundle["integrity"] = _stub_integrity(body)
    return bundle


def summarize(bundle: dict[str, Any]) -> str:
    return str(bundle.get("summary", "DUE bundle"))
