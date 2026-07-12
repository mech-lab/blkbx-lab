import hashlib
from typing import Any
from .canonical import canonicalize
from .signing import DEV_SECRET

def verify_receipt(receipt_data: dict[str, Any]) -> dict[str, Any]:
    """Verify a receipt's schema, hash, and signature."""
    integrity = receipt_data.get("integrity")
    if not integrity:
        return {"valid": False, "reason": "Missing integrity block"}
        
    data_to_verify = {k: v for k, v in receipt_data.items() if k != "integrity"}
    canonical_bytes = canonicalize(data_to_verify)
    canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()
    
    expected_hash = f"sha256:{canonical_hash}"
    if integrity.get("hash") != expected_hash:
        return {"valid": False, "reason": "Hash mismatch"}
        
    # Mock signature verification
    signature_input = canonical_bytes + DEV_SECRET
    expected_signature = f"dev-signature:{hashlib.sha512(signature_input).hexdigest()[:64]}"
    
    if integrity.get("signature") != expected_signature:
        return {"valid": False, "reason": "Signature mismatch"}
        
    return {"valid": True, "reason": "Valid"}
