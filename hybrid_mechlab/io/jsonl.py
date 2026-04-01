"""JSON and JSONL artifact helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load(path: str) -> Any:
    target = Path(path)
    raw = target.read_text(encoding="utf-8")
    if target.suffix == ".jsonl":
        return [json.loads(line) for line in raw.splitlines() if line.strip()]
    return json.loads(raw)


def save(path: str, data: Any) -> str:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix == ".jsonl":
        if not isinstance(data, list):
            raise ValueError("jsonl export expects a list of records")
        payload = "\n".join(json.dumps(item, sort_keys=True) for item in data)
    else:
        payload = json.dumps(data, indent=2, sort_keys=True)
    target.write_text(payload, encoding="utf-8")
    return str(target)
