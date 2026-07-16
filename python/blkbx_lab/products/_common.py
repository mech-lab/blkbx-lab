from __future__ import annotations

import copy
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def issued_at() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stub_integrity(payload: dict[str, Any]) -> dict[str, Any]:
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return {
        "digest": f"sha256:{digest}",
        "signature_algorithm": "stub-v1",
        "signature": None,
        "core_binding": None,
    }


def event(event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"event_type": event_type, "payload": payload or {}}


def clone(payload: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(payload)


def new_identifier(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def normalized_human_review(human_review: dict[str, Any] | None) -> dict[str, Any]:
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
        "reviewed_at": human_review.get("reviewed_at", issued_at()),
    }


def refresh_integrity(document: dict[str, Any]) -> dict[str, Any]:
    updated = clone(document)
    body = {key: value for key, value in updated.items() if key != "integrity"}
    updated["integrity"] = stub_integrity(body)
    return updated


def with_human_review(document: dict[str, Any], human_review: dict[str, Any] | None) -> dict[str, Any]:
    if not human_review:
        return clone(document)
    updated = clone(document)
    review = normalized_human_review(human_review)
    updated["human_review"] = review
    updated.setdefault("event_trail", []).append(event("human_review_recorded", review))
    return refresh_integrity(updated)
