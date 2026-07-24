"""BLKBXS schema loading and validation."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

SCHEMA_FILES = {
    "blkbxs.ubr.receipt.v1": "blkbxs.ubr.receipt.v1.schema.json",
    "blkbxs.ubr.bundle.v1": "blkbxs.ubr.bundle.v1.schema.json",
    "blkbxs.ubr.verifier_report.v1": "blkbxs.ubr.verifier_report.v1.schema.json",
}


def load_schema(schema_name: str) -> dict[str, Any]:
    filename = SCHEMA_FILES.get(schema_name)
    if filename is None:
        raise ValueError(f"Unknown schema: {schema_name}")
    return json.loads(files("blkbx_lab.products.blkbxs.schemas").joinpath(filename).read_text(encoding="utf-8"))


def validate(payload: dict[str, Any], schema_name: str | None = None) -> bool:
    name = schema_name or payload.get("schema") or (
        "blkbxs.ubr.receipt.v1" if payload.get("type") == "UniversalBankingReceipt" else None
    )
    if not name:
        raise ValueError("schema_name is required when payload does not contain a schema field")
    validator = Draft7Validator(load_schema(name), format_checker=FormatChecker())
    validator.validate(payload)
    return True


__all__ = ["SCHEMA_FILES", "load_schema", "validate"]

