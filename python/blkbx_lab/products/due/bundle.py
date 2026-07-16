"""DUE bundle export."""

from __future__ import annotations

from importlib.resources import files
import uuid
from typing import Any

from .._common import issued_at, stub_integrity

BUNDLE_SCHEMA_ID = "due.dispute_bundle.v1"
INSTITUTIONAL_QUESTION = "Can this AI-assisted action survive challenge, dispute, discovery, privilege review, disclosure review, and liability scrutiny?"


def available_templates() -> list[str]:
    return sorted(path.name for path in files("due.bundles").iterdir() if path.name.endswith(".md"))


def load_template(template_name: str) -> str:
    return files("due.bundles").joinpath(template_name).read_text(encoding="utf-8")


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
        "generated_at": issued_at(),
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
    bundle["integrity"] = stub_integrity(body)
    return bundle


def summarize(bundle: dict[str, Any]) -> str:
    return str(bundle.get("summary", "DUE bundle"))


__all__ = [
    "BUNDLE_SCHEMA_ID",
    "INSTITUTIONAL_QUESTION",
    "available_templates",
    "export",
    "load_template",
    "summarize",
]
