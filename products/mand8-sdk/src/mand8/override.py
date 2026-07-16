"""MAND8 override recording."""

from __future__ import annotations

from typing import Any

from .receipt import append_event


def record(
    receipt: dict[str, Any],
    override_id: str,
    override_type: str,
    reason: str,
    overridden_by: str,
    effective_date: str,
    outcome: str = "manual_override_applied",
    details: dict[str, Any] | None = None,
    human_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    review = human_review
    if review is None and overridden_by and not overridden_by.startswith("system:"):
        review = {
            "reviewer": overridden_by,
            "notes": reason,
            "status": "reviewed",
        }
    return append_event(
        receipt,
        "override_recorded",
        {
            "override_id": override_id,
            "override_type": override_type,
            "reason": reason,
            "overridden_by": overridden_by,
            "effective_date": effective_date,
            "outcome": outcome,
            "details": details or {},
        },
        human_review=review,
    )
