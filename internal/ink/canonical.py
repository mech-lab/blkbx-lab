import json
from typing import Any

def canonicalize(data: dict[str, Any]) -> bytes:
    """Deterministic JSON canonicalization (JCS-RFC8785 style)."""
    return json.dumps(data, separators=(',', ':'), sort_keys=True, ensure_ascii=False).encode('utf-8')

import hashlib
from pathlib import Path

def hash_bytes(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"

def hash_text(text: str) -> str:
    return hash_bytes(text.encode("utf-8"))

def hash_file(path: str | Path) -> str:
    return hash_bytes(Path(path).read_bytes())

def canonical_json_hash(obj: dict[str, Any]) -> str:
    return hash_bytes(canonicalize(obj))
