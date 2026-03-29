from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from .artifacts import ARTIFACT_FILENAMES, ArtifactRef, Manifest, artifact_path_for_type
from .ids import derive_artifact_id, file_sha256


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def build_manifest(run_dir: str | Path, trace_id: str, producer: str, *, created_at: str | None = None) -> Manifest:
    root = Path(run_dir)
    artifacts: list[ArtifactRef] = []
    for artifact_type, filename in ARTIFACT_FILENAMES.items():
        if artifact_type == "mair_manifest":
            continue
        path = root / filename
        if not path.exists():
            continue
        content_hash = file_sha256(path)
        artifacts.append(
            ArtifactRef(
                artifact_type=artifact_type,
                path=filename,
                artifact_id=derive_artifact_id(artifact_type, content_hash),
                content_hash=content_hash,
                byte_size=path.stat().st_size,
            )
        )
    return Manifest(
        trace_id=trace_id,
        producer=producer,
        created_at=created_at or _utc_now(),
        artifacts=artifacts,
    )


def write_manifest(run_dir: str | Path, trace_id: str, producer: str, *, created_at: str | None = None) -> Path:
    root = Path(run_dir)
    manifest = build_manifest(root, trace_id=trace_id, producer=producer, created_at=created_at)
    target = artifact_path_for_type(root, "mair_manifest")
    target.write_text(json.dumps(manifest.as_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return target


def load_manifest(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
