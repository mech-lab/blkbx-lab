"""MAND8 receipt primitives."""

from __future__ import annotations

import copy
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

SCHEMA_ID = "mand8.risk_receipt.v1"


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _issued_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stub_integrity(payload: dict[str, Any]) -> dict[str, Any]:
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return {
        "digest": f"sha256:{digest}",
        "signature_algorithm": "stub-v1",
        "signature": None,
        "core_binding": None,
    }


def _event(event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"event_type": event_type, "payload": payload or {}}


def _clone(payload: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(payload)


def refresh_integrity(receipt: dict[str, Any]) -> dict[str, Any]:
    updated = _clone(receipt)
    body = {key: value for key, value in updated.items() if key != "integrity"}
    updated["integrity"] = _stub_integrity(body)
    return updated


def _normalized_human_review(human_review: dict[str, Any] | None) -> dict[str, Any]:
    if not human_review:
        return {
            "reviewer": None,
            "notes": None,
            "status": "not_reviewed",
            "reviewed_at": None,
        }
    return {
        "reviewer": human_review.get("reviewer"),
        "notes": human_review.get("notes"),
        "status": human_review.get("status", "reviewed"),
        "reviewed_at": human_review.get("reviewed_at", _issued_at()),
    }


def with_human_review(receipt: dict[str, Any], human_review: dict[str, Any] | None) -> dict[str, Any]:
    if not human_review:
        return _clone(receipt)
    updated = _clone(receipt)
    review = _normalized_human_review(human_review)
    updated["human_review"] = review
    updated.setdefault("event_trail", []).append(_event("human_review_recorded", review))
    return refresh_integrity(updated)


def append_event(
    receipt: dict[str, Any],
    event_type: str,
    payload: dict[str, Any] | None = None,
    human_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    updated = _clone(receipt)
    updated.setdefault("event_trail", []).append(_event(event_type, payload))
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
        "receipt_id": receipt_id or f"rcpt_{uuid.uuid4().hex[:12]}",
        "action_id": action_id or f"act_{uuid.uuid4().hex[:12]}",
        "issued_at": _issued_at(),
        "domain_context": domain_context or {},
        "event_trail": [_event(event_type, payload)],
        "human_review": _normalized_human_review(None),
    }
    receipt = dict(body)
    receipt["integrity"] = _stub_integrity(body)
    return with_human_review(receipt, human_review)
