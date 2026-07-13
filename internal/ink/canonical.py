from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonicalize(data: dict[str, Any] | list[Any]) -> bytes:
    return json.dumps(data, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def digest_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_bytes(data: bytes) -> str:
    return f"sha256:{digest_hex(data)}"


def hash_text(text: str) -> str:
    return hash_bytes(text.encode("utf-8"))


def hash_file(path: str | Path) -> str:
    return hash_bytes(Path(path).read_bytes())


def canonical_json_hash(obj: dict[str, Any] | list[Any]) -> str:
    return hash_bytes(canonicalize(obj))


def strip_hash_prefix(value: str) -> str:
    if not value.startswith("sha256:"):
        raise ValueError(f"expected sha256 digest, got {value!r}")
    return value.split(":", 1)[1]


def hash_bytes_raw(data: bytes) -> str:
    return digest_hex(data)


def tlv_field(field_id: int, value: bytes) -> bytes:
    return field_id.to_bytes(2, "big") + len(value).to_bytes(4, "big") + value
