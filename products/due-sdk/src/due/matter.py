"""DUE matter binding."""

from __future__ import annotations

from typing import Any

from .receipt import append_event


def bind(
    receipt: dict[str, Any],
    matter_id: str,
    jurisdiction: str,
    parties: dict[str, str],
    case_type: str,
    case_number: str | None = None,
    filing_date: str | None = None,
    matter_status: str = "active",
    human_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = {
        "matter_id": matter_id,
        "jurisdiction": jurisdiction,
        "parties": parties,
        "case_type": case_type,
        "case_number": case_number,
        "filing_date": filing_date,
        "matter_status": matter_status,
    }
    return append_event(
        receipt,
        "matter_bound",
        {"matter_id": matter_id, "jurisdiction": jurisdiction},
        context_updates=context,
        human_review=human_review,
    )
