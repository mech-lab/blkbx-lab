import json
from typing import Any

def canonicalize(data: dict[str, Any]) -> bytes:
    """Deterministic JSON canonicalization (JCS-RFC8785 style)."""
    return json.dumps(data, separators=(',', ':'), sort_keys=True, ensure_ascii=False).encode('utf-8')
