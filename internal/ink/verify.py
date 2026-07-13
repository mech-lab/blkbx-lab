from __future__ import annotations

from typing import Any

from .v2 import verify_receipt_payload


def verify_receipt(receipt_data: dict[str, Any]) -> dict[str, Any]:
    return verify_receipt_payload(receipt_data)
