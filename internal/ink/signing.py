from __future__ import annotations

from typing import Any

from .v2 import DEV_KEY_ID, sign_receipt_payload


def sign_receipt(
    receipt_data: dict[str, Any],
    *,
    demo_signer: bool = True,
    signer_seed: bytes | None = None,
) -> dict[str, Any]:
    return sign_receipt_payload(receipt_data, demo_signer=demo_signer, signer_seed=signer_seed)
