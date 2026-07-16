"""DUE authority checks."""

from __future__ import annotations

from typing import Any

from .receipt import append_event


def check(
    receipt: dict[str, Any],
    authority_id: str,
    authority_name: str,
    jurisdiction: str,
    authority_type: str,
    basis: str | None = None,
    credentials: dict[str, Any] | None = None,
    human_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    authority_context = {
        "authority_id": authority_id,
        "authority_name": authority_name,
        "jurisdiction": jurisdiction,
        "authority_type": authority_type,
        "basis": basis,
        "credentials": credentials or {},
    }
    return append_event(
        receipt,
        "authority_checked",
        authority_context,
        context_updates={"authority": authority_context},
        human_review=human_review,
    )
