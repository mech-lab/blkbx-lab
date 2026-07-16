"""DUE legal action recording."""

from __future__ import annotations

from typing import Any

from .receipt import append_event


def record(
    receipt: dict[str, Any],
    action_name: str,
    action_type: str,
    description: str,
    legal_basis: str,
    materiality: str = "medium",
    adverse_action: bool = False,
    chain_of_custody_ref: str | None = None,
    human_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "action_name": action_name,
        "action_type": action_type,
        "description": description,
        "legal_basis": legal_basis,
        "materiality": materiality,
        "adverse_action": adverse_action,
        "chain_of_custody_ref": chain_of_custody_ref,
    }
    return append_event(
        receipt,
        "ai_assisted_legal_action_recorded",
        payload,
        context_updates={
            "action_name": action_name,
            "action_type": action_type,
            "materiality": materiality,
        },
        human_review=human_review,
    )
