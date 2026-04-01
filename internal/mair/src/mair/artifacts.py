from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ARTIFACT_FILENAMES: dict[str, str] = {
    "mair_semantic_trace": "mair_semantic_trace.v1.jsonl",
    "mair_graph_ir": "mair_graph_ir.v1.json",
    "mair_numeric_lowering": "mair_numeric_lowering.v1.json",
    "blt_codes": "blt_codes.v1.parquet",
    "tract_state_snapshot": "tract_state_snapshot.v1.parquet",
    "grouped_clt_bundle": "grouped_clt_bundle.v1.json",
    "topology_summary": "topology_summary.v1.json",
    "offline_topology_report": "offline_topology_report.v1.json",
    "backend_comparison": "backend_comparison.v1.json",
    "replacement_eval": "replacement_eval.v1.json",
    "concept_lineage_bundle": "concept_lineage_bundle.v1.json",
    "intervention_sweep": "intervention_sweep.v1.jsonl",
    "assurance_receipt": "assurance_receipt.v1.json",
    "mair_manifest": "mair_manifest.v1.json",
}

JSON_ARTIFACTS = {
    "mair_graph_ir",
    "mair_numeric_lowering",
    "grouped_clt_bundle",
    "topology_summary",
    "offline_topology_report",
    "backend_comparison",
    "replacement_eval",
    "concept_lineage_bundle",
    "assurance_receipt",
    "mair_manifest",
}
JSONL_ARTIFACTS = {"mair_semantic_trace", "intervention_sweep"}
PARQUET_ARTIFACTS = {"blt_codes", "tract_state_snapshot"}

PARQUET_REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "blt_codes": (
        "trace_id",
        "token_index",
        "block_id",
        "code_group",
        "reconstruction_error",
        "bridge_strength",
    ),
    "tract_state_snapshot": (
        "trace_id",
        "token_index",
        "block_id",
        "stage",
        "state_mean",
        "state_norm",
        "bridge_strength",
        "gate_strength",
    ),
}


@dataclass(slots=True)
class ArtifactRef:
    artifact_type: str
    path: str
    artifact_id: str
    content_hash: str
    schema_version: int = 1
    byte_size: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Manifest:
    trace_id: str
    producer: str
    created_at: str
    artifacts: list[ArtifactRef] = field(default_factory=list)
    schema_version: int = 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "producer": self.producer,
            "created_at": self.created_at,
            "schema_version": self.schema_version,
            "artifacts": [artifact.as_dict() for artifact in self.artifacts],
        }


def artifact_type_from_filename(filename: str) -> str:
    for artifact_type, expected in ARTIFACT_FILENAMES.items():
        if filename == expected:
            return artifact_type
    raise KeyError(f"unknown MAIR artifact filename: {filename}")


def artifact_path_for_type(run_dir: str | Path, artifact_type: str) -> Path:
    try:
        filename = ARTIFACT_FILENAMES[artifact_type]
    except KeyError as exc:
        raise KeyError(f"unknown MAIR artifact type: {artifact_type}") from exc
    return Path(run_dir) / filename
