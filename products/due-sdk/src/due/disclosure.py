"""DUE disclosure recording."""

from __future__ import annotations

from typing import Any

from .receipt import append_event


def record(
    receipt: dict[str, Any],
    disclosure_id: str,
    disclosure_type: str,
    recipient: str,
    content_summary: str,
    status: str,
    disclosed_on: str | None = None,
    method: str | None = None,
    human_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    disclosure_context = {
        "disclosure_id": disclosure_id,
        "disclosure_type": disclosure_type,
        "recipient": recipient,
        "content_summary": content_summary,
        "status": status,
        "disclosed_on": disclosed_on,
        "method": method,
    }
    return append_event(
        receipt,
        "disclosure_recorded",
        disclosure_context,
        context_updates={"disclosure": disclosure_context},
        human_review=human_review,
    )
