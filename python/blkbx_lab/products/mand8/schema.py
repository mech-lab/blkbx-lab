"""MAND8 schema loading and validation."""

from __future__ import annotations

from importlib.resources import files
import json
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

SCHEMA_FILES = {
    "mand8.risk_receipt.v1": "mand8.risk_receipt.v1.schema.json",
    "mand8.exposure_unit.v1": "mand8.exposure_unit.v1.schema.json",
    "mand8.authority_receipt.v1": "mand8.authority_receipt.v1.schema.json",
    "mand8.control_receipt.v1": "mand8.control_receipt.v1.schema.json",
    "mand8.incident_receipt.v1": "mand8.incident_receipt.v1.schema.json",
    "mand8.bundle.v1": "mand8.bundle.v1.schema.json",
}


def available_schemas() -> list[str]:
    return sorted(SCHEMA_FILES)


def load_schema(schema_name: str) -> dict[str, Any]:
    filename = SCHEMA_FILES.get(schema_name)
    if filename is None:
        raise ValueError(f"Unknown schema: {schema_name}")
    return json.loads(files("mand8.schemas").joinpath(filename).read_text(encoding="utf-8"))


def validate(payload: dict[str, Any], schema_name: str | None = None) -> bool:
    name = schema_name or payload.get("schema")
    if not name:
        raise ValueError("schema_name is required when payload does not contain a schema field")
    validator = Draft7Validator(load_schema(name), format_checker=FormatChecker())
    validator.validate(payload)
    return True


__all__ = ["SCHEMA_FILES", "available_schemas", "load_schema", "validate"]
