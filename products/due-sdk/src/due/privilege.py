"""DUE privilege recording."""

from __future__ import annotations

from typing import Any

from .receipt import append_event


def record(
    receipt: dict[str, Any],
    privilege_id: str,
    privilege_type: str,
    holder: str,
    basis: str,
    scope: str | None = None,
    materiality: str = "high",
    human_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    privilege_context = {
        "privilege_id": privilege_id,
        "privilege_type": privilege_type,
        "holder": holder,
        "basis": basis,
        "scope": scope,
        "materiality": materiality,
    }
    return append_event(
        receipt,
        "privilege_recorded",
        privilege_context,
        context_updates={"privilege": privilege_context},
        human_review=human_review,
    )
