"""MAND8 incident recording."""

from __future__ import annotations

from typing import Any

from .receipt import append_event


def record(
    receipt: dict[str, Any],
    incident_id: str,
    incident_type: str,
    severity: str,
    description: str,
    claims_impact: str = "undetermined",
    reviewer: str | None = None,
    resolution: dict[str, Any] | None = None,
    human_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    review = human_review
    if review is None and reviewer:
        review = {
            "reviewer": reviewer,
            "notes": f"Incident reviewed: {description}",
            "status": "reviewed",
        }
    return append_event(
        receipt,
        "incident_recorded",
        {
            "incident_id": incident_id,
            "incident_type": incident_type,
            "severity": severity,
            "description": description,
            "claims_impact": claims_impact,
            "resolution": resolution or {},
        },
        human_review=review,
    )


__all__ = ["record"]
