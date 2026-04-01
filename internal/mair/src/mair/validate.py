from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from jsonschema.validators import validator_for

from .artifacts import (
    JSON_ARTIFACTS,
    JSONL_ARTIFACTS,
    PARQUET_ARTIFACTS,
    PARQUET_REQUIRED_COLUMNS,
    artifact_type_from_filename,
)


def _schema_dir() -> Path:
    packaged = Path(__file__).resolve().parent / "schemas"
    if packaged.exists():
        return packaged
    return Path(__file__).resolve().parents[2] / "schemas"


def _load_schema(schema_name: str) -> dict[str, Any]:
    path = _schema_dir() / schema_name
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_payload(payload: Any, schema_name: str) -> None:
    schema = _load_schema(schema_name)
    validator_cls = validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.path))
    if errors:
        joined = "; ".join(error.message for error in errors)
        raise ValueError(f"schema validation failed for {schema_name}: {joined}")


def validate_artifact(path: str | Path, artifact_type: str | None = None) -> None:
    artifact_path = Path(path)
    kind = artifact_type or artifact_type_from_filename(artifact_path.name)
    if kind in JSON_ARTIFACTS:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        _validate_payload(payload, f"{kind}.v1.schema.json")
        return
    if kind in JSONL_ARTIFACTS:
        with artifact_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                payload = json.loads(line)
                try:
                    _validate_payload(payload, f"{kind}.v1.schema.json")
                except ValueError as exc:
                    raise ValueError(f"{artifact_path.name}:{line_number}: {exc}") from exc
        return
    if kind in PARQUET_ARTIFACTS:
        table = pq.read_table(artifact_path)
        required = PARQUET_REQUIRED_COLUMNS[kind]
        missing = [column for column in required if column not in table.column_names]
        if missing:
            raise ValueError(f"parquet validation failed for {artifact_path.name}: missing columns {missing}")
        return
    raise KeyError(f"unsupported MAIR artifact type: {kind}")


def validate_manifest(path: str | Path) -> dict[str, Any]:
    manifest_path = Path(path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    _validate_payload(payload, "mair_manifest.v1.schema.json")
    for artifact in payload.get("artifacts", []):
        validate_artifact(manifest_path.parent / artifact["path"], artifact["artifact_type"])
    return payload
