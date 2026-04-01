from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

import pyarrow.parquet as pq

from .artifacts import JSON_ARTIFACTS, JSONL_ARTIFACTS, PARQUET_ARTIFACTS
from .validate import validate_manifest


def _load_artifact_payload(path: Path, artifact_type: str) -> Any:
    if artifact_type in JSON_ARTIFACTS:
        return json.loads(path.read_text(encoding="utf-8"))
    if artifact_type in JSONL_ARTIFACTS:
        with path.open("r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]
    if artifact_type in PARQUET_ARTIFACTS:
        return pq.read_table(path).to_pylist()
    raise KeyError(f"unsupported MAIR artifact type: {artifact_type}")


def iter_artifacts(manifest_path: str | Path) -> Iterator[tuple[str, Any]]:
    manifest_file = Path(manifest_path)
    manifest = validate_manifest(manifest_file)
    root = manifest_file.parent
    for artifact in manifest["artifacts"]:
        yield artifact["artifact_type"], _load_artifact_payload(root / artifact["path"], artifact["artifact_type"])


def load_artifact_bundle(manifest_path: str | Path) -> dict[str, Any]:
    manifest_file = Path(manifest_path)
    manifest = validate_manifest(manifest_file)
    return {
        "manifest": manifest,
        "artifacts": {artifact_type: payload for artifact_type, payload in iter_artifacts(manifest_file)},
    }


def load_artifact_by_type(manifest_path: str | Path, artifact_type: str) -> Any:
    manifest_file = Path(manifest_path)
    manifest = validate_manifest(manifest_file)
    root = manifest_file.parent
    for artifact in manifest["artifacts"]:
        if artifact["artifact_type"] == artifact_type:
            return _load_artifact_payload(root / artifact["path"], artifact_type)
    raise KeyError(f"artifact type not present in manifest: {artifact_type}")
