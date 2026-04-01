from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from blt._mair import ensure_mair_importable

ensure_mair_importable()
from mair.hydrate import load_artifact_bundle  # noqa: E402
from mair.ids import stable_hash  # noqa: E402

try:  # pragma: no cover - exercised when hybrid_mechlab is installed
    from hybrid_mechlab.io.manifests import TRACE_SCHEMA_KEYS, serialize_trace_record
except Exception:  # pragma: no cover - default path in BLT-only environments
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


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _block_ids(graph_ir: dict[str, Any], blt_code_rows: list[dict[str, Any]]) -> list[str]:
    blocks = {str(row["block_id"]) for row in blt_code_rows if row.get("block_id") is not None}
    if not blocks:
        blocks = {
            str(node["block_id"])
            for node in graph_ir.get("nodes", [])
            if isinstance(node, dict) and node.get("block_id") is not None
        }
    return sorted(blocks)


def _capture_surfaces(artifact_payloads: dict[str, Any]) -> list[str]:
    capture: list[str] = []
    if "blt_codes" in artifact_payloads:
        capture.append("codes")
    if "topology_summary" in artifact_payloads:
        capture.append("sketches")
    if "tract_state_snapshot" in artifact_payloads or "mair_semantic_trace" in artifact_payloads:
        capture.append("transport")
    if "grouped_clt_bundle" in artifact_payloads:
        capture.append("grouped_clt")
    return capture


def _transport_digest(
    *,
    backend: str,
    topology_summary: dict[str, Any],
    semantic_rows: list[dict[str, Any]],
    tract_rows: list[dict[str, Any]],
    blt_code_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    bridge_crossings = sum(1 for row in semantic_rows if row.get("op") == "BridgeApply")
    local_steps = len(tract_rows) if tract_rows else sum(1 for row in semantic_rows if row.get("op") == "StateUpdate")
    summary_metrics = topology_summary.get("summary_metrics") or {}
    retention_score = topology_summary.get("tract_retention")
    if retention_score is None:
        retention_score = max(0.0, 1.0 - _mean([float(row["reconstruction_error"]) for row in blt_code_rows]))
    return {
        "local_steps": int(local_steps),
        "bridge_crossings": int(bridge_crossings),
        "retention_score": round(float(retention_score), 6),
        "backend": backend,
        "component_count": int(summary_metrics.get("component_count", 0)),
    }


def _signed_sketch(
    topology_summary: dict[str, Any],
    intervention_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    summary_metrics = topology_summary.get("summary_metrics") or {}
    component_count = int(summary_metrics.get("component_count", 0))
    mean_degree = float(summary_metrics.get("mean_degree", 0.0))
    return {
        "positive_components": max(component_count, 1),
        "negative_components": 0,
        "cancellation_pairs": len(intervention_rows),
        "cycle_hint": max(int(round(mean_degree)) - 1, 0),
    }


def _schedule_summary(
    *,
    family: str,
    block_ids: list[str],
    topology_summary: dict[str, Any],
) -> str:
    return (
        f"family={family}; blocks={len(block_ids)}; "
        f"bridge_policy={topology_summary.get('bridge_policy', 'unknown')}; "
        f"intervention_axis={topology_summary.get('intervention_axis', 'unknown')}"
    )


def _reproducibility_manifest(
    *,
    model: str,
    profile_name: str,
    family: str,
    backend: str,
    schedule: str,
) -> dict[str, Any]:
    schedule_hash = stable_hash(
        {
            "model": model,
            "profile_name": profile_name,
            "family": family,
            "backend": backend,
            "schedule": schedule,
        }
    )[:16]
    return {
        "model": model,
        "profile_name": profile_name,
        "family": family,
        "backend": backend,
        "schedule_hash": schedule_hash,
    }


def _sparse_codes(blt_code_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_block: dict[str, list[dict[str, Any]]] = {}
    for row in blt_code_rows:
        by_block.setdefault(str(row["block_id"]), []).append(row)
    records: list[dict[str, Any]] = []
    for block_id, members in sorted(by_block.items()):
        records.append(
            {
                "hook": f"{block_id}.post_d3",
                "feature_ids": [0, 1, 2, 3],
                "feature_values": [
                    _mean([float(member[column]) for member in members])
                    for column in ("code_0", "code_1", "code_2", "code_3")
                ],
            }
        )
    return records


def build_hybrid_mechlab_record(manifest_path: str | Path) -> dict[str, Any]:
    bundle = load_artifact_bundle(manifest_path)
    manifest = bundle["manifest"]
    artifacts = bundle["artifacts"]
    graph_ir = artifacts["mair_graph_ir"]
    numeric_lowering = artifacts.get("mair_numeric_lowering", {})
    topology_summary = artifacts.get("topology_summary", {})
    semantic_rows = artifacts.get("mair_semantic_trace", [])
    tract_rows = artifacts.get("tract_state_snapshot", [])
    blt_code_rows = artifacts.get("blt_codes", [])
    intervention_rows = artifacts.get("intervention_sweep", [])

    family = str(graph_ir.get("model_family", "unknown-family"))
    backend = str(graph_ir.get("capture_backend") or numeric_lowering.get("backend") or "unknown-backend")
    profile_name = str(graph_ir.get("profile_id") or numeric_lowering.get("profile_id") or graph_ir.get("model_variant", "unknown-profile"))
    model = str(graph_ir.get("model_variant", "unknown-model"))
    block_ids = _block_ids(graph_ir, blt_code_rows)
    schedule = _schedule_summary(family=family, block_ids=block_ids, topology_summary=topology_summary)

    record = {
        "trace_id": manifest["trace_id"],
        "prompt_count": 1,
        "profile_name": profile_name,
        "family": family,
        "backend": backend,
        "schedule": schedule,
        "capture": _capture_surfaces(artifacts),
        "transport_digest": _transport_digest(
            backend=backend,
            topology_summary=topology_summary,
            semantic_rows=semantic_rows,
            tract_rows=tract_rows,
            blt_code_rows=blt_code_rows,
        ),
        "signed_sketch": _signed_sketch(topology_summary, intervention_rows),
        "reproducibility_manifest": _reproducibility_manifest(
            model=model,
            profile_name=profile_name,
            family=family,
            backend=backend,
            schedule=schedule,
        ),
        "sparse_codes": _sparse_codes(blt_code_rows),
    }
    return serialize_trace_record(record)


def write_hybrid_mechlab_record(
    manifest_path: str | Path,
    *,
    output_path: str | Path | None = None,
) -> Path:
    manifest_file = Path(manifest_path)
    record = build_hybrid_mechlab_record(manifest_file)
    target = (
        Path(output_path)
        if output_path is not None
        else manifest_file.parent / f"{record['trace_id']}.hybrid_mechlab_trace.json"
    )
    target.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    return target
