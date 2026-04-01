"""Trace manifest helpers."""

from __future__ import annotations

from typing import Any


TRACE_SCHEMA_KEYS = (
    "trace_id",
    "prompt_count",
    "profile_name",
    "family",
    "backend",
    "schedule",
    "capture",
    "transport_digest",
    "signed_sketch",
    "reproducibility_manifest",
    "sparse_codes",
)


def serialize_trace_record(record: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in TRACE_SCHEMA_KEYS if key not in record]
    if missing:
        raise ValueError(f"trace record missing required keys: {missing}")
    return {key: record[key] for key in TRACE_SCHEMA_KEYS}
