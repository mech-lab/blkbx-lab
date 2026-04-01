from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def derive_artifact_id(artifact_type: str, content_hash: str, schema_version: int = 1) -> str:
    seed = f"{artifact_type}:{schema_version}:{content_hash}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return f"{artifact_type}-{digest[:16]}"
