"""MAND8 receipt primitives."""

from __future__ import annotations

from typing import Any

from .._common import clone, event, issued_at, new_identifier, normalized_human_review, refresh_integrity, with_human_review

SCHEMA_ID = "mand8.risk_receipt.v1"


def append_event(
    receipt: dict[str, Any],
    event_type: str,
    payload: dict[str, Any] | None = None,
    human_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    updated = clone(receipt)
    updated.setdefault("event_trail", []).append(event(event_type, payload))
    updated = refresh_integrity(updated)
    return with_human_review(updated, human_review)


def create(
    domain_context: dict[str, Any] | None = None,
    event_type: str = "receipt_created",
    payload: dict[str, Any] | None = None,
    human_review: dict[str, Any] | None = None,
    action_id: str | None = None,
    receipt_id: str | None = None,
) -> dict[str, Any]:
    body = {
        "schema": SCHEMA_ID,
        "receipt_id": receipt_id or new_identifier("rcpt"),
        "action_id": action_id or new_identifier("act"),
        "issued_at": issued_at(),
        "domain_context": domain_context or {},
        "event_trail": [event(event_type, payload)],
        "human_review": normalized_human_review(None),
    }
    receipt = dict(body)
    receipt["integrity"] = refresh_integrity(body)["integrity"]
    return with_human_review(receipt, human_review)


__all__ = [
    "SCHEMA_ID",
    "append_event",
    "create",
    "refresh_integrity",
    "with_human_review",
]
