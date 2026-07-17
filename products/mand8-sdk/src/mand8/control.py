"""MAND8 risk-control recording."""

from __future__ import annotations

from typing import Any

from .receipt import append_event


def record(
    receipt: dict[str, Any],
    control_id: str,
    control_name: str,
    status: str,
    evidence_ref: str = "",
    control_type: str = "risk_control",
    details: dict[str, Any] | None = None,
    human_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return append_event(
        receipt,
        "control_check_recorded",
        {
            "control_id": control_id,
            "control_name": control_name,
            "status": status,
            "control_type": control_type,
            "evidence_ref": evidence_ref,
            "details": details or {},
        },
        context_updates={
            "last_control_id": control_id,
            "last_control_status": status,
        },
        human_review=human_review,
    )
