import hashlib
from typing import Any
from .canonical import canonicalize

# Dev key for demo purposes
DEV_KEY_ID = "ed25519:dev"
DEV_SECRET = b"dev-secret-key-do-not-use-in-prod"

def sign_receipt(receipt_data: dict[str, Any]) -> dict[str, Any]:
    """Sign a receipt using the dev key."""
    # Remove existing integrity block if present
    data_to_sign = {k: v for k, v in receipt_data.items() if k != "integrity"}
    
    canonical_bytes = canonicalize(data_to_sign)
    canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()
    
    # Mock signature for demo
    signature_input = canonical_bytes + DEV_SECRET
    signature = f"ed25519:{hashlib.sha512(signature_input).hexdigest()[:64]}"
    
    receipt_data["integrity"] = {
        "canonicalization": "jcs-rfc8785",
        "hash": f"sha256:{canonical_hash}",
        "signature": signature
    }
    return receipt_data
