"""MAND8 receipt primitives."""

from __future__ import annotations

from typing import Any

from .._common import clone, event, issued_at, new_identifier, normalized_human_review, refresh_integrity, with_human_review

SCHEMA_ID = "mand8.risk_receipt.v1"


def case_identifier(document: dict[str, Any]) -> str | None:
    return document.get("case_id") or document.get("domain_context", {}).get("case_id")


def _payload_with_case_id(case_id: str | None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if case_id is None:
        return clone(payload or {})
    updated = clone(payload or {})
    updated.setdefault("case_id", case_id)
    return updated


def append_event(
    receipt: dict[str, Any],
    event_type: str,
    payload: dict[str, Any] | None = None,
    context_updates: dict[str, Any] | None = None,
    human_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    updated = clone(receipt)
    if context_updates:
        updated.setdefault("domain_context", {}).update(context_updates)
    case_id = case_identifier(updated)
    updated.setdefault("event_trail", []).append(event(event_type, _payload_with_case_id(case_id, payload)))
    updated = refresh_integrity(updated)
    return with_human_review(updated, human_review)


def create(
    domain_context: dict[str, Any] | None = None,
    event_type: str = "receipt_created",
    payload: dict[str, Any] | None = None,
    human_review: dict[str, Any] | None = None,
    action_id: str | None = None,
    receipt_id: str | None = None,
    case_id: str | None = None,
) -> dict[str, Any]:
    context = clone(domain_context or {})
    resolved_case_id = case_id or context.get("case_id") or new_identifier("case")
    context["case_id"] = resolved_case_id
    body = {
        "schema": SCHEMA_ID,
        "receipt_id": receipt_id or new_identifier("rcpt"),
        "action_id": action_id or new_identifier("act"),
        "case_id": resolved_case_id,
        "issued_at": issued_at(),
        "domain_context": context,
        "event_trail": [event(event_type, _payload_with_case_id(resolved_case_id, payload))],
        "human_review": normalized_human_review(None),
    }
    receipt = dict(body)
    receipt["integrity"] = refresh_integrity(body)["integrity"]
    return with_human_review(receipt, human_review)


__all__ = [
    "SCHEMA_ID",
    "append_event",
    "case_identifier",
    "create",
    "refresh_integrity",
    "with_human_review",
]
