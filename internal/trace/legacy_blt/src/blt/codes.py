from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from ._mair import ensure_mair_importable

ensure_mair_importable()
from mair.manifest import load_manifest, write_manifest  # noqa: E402


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _group_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["code_group"]), []).append(row)
    return grouped


def _read_blt_codes(path: str | Path) -> list[dict[str, Any]]:
    table = pq.read_table(path)
    return table.to_pylist()


def fit_grouped_clt_rows(rows: list[dict[str, Any]], trace_id: str, model_family: str, model_variant: str) -> dict[str, Any]:
    grouped = _group_rows(rows)
    groups: list[dict[str, Any]] = []
    for group_id, members in sorted(grouped.items()):
        centroid = [
            _mean([float(member[column]) for member in members])
            for column in ("code_0", "code_1", "code_2", "code_3")
        ]
        groups.append(
            {
                "group_id": group_id,
                "size": len(members),
                "reconstruction_divergence": _mean([float(member["reconstruction_error"]) for member in members]),
                "bridge_dependence": _mean([float(member["bridge_strength"]) for member in members]),
                "centroid": centroid,
            }
        )
    return {
        "trace_id": trace_id,
        "model_family": model_family,
        "model_variant": model_variant,
        "groups": groups,
        "summary_metrics": {
            "group_count": len(groups),
            "mean_reconstruction_divergence": _mean([group["reconstruction_divergence"] for group in groups]),
            "mean_bridge_dependence": _mean([group["bridge_dependence"] for group in groups]),
        },
    }


def build_intervention_sweep(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for group in bundle["groups"]:
        for strength in (0.25, 0.5, 0.75):
            rows.append(
                {
                    "trace_id": bundle["trace_id"],
                    "group_id": group["group_id"],
                    "intervention": f"scale:{strength}",
                    "metric": "bridge_dependence",
                    "delta": round(-group["bridge_dependence"] * strength, 6),
                    "metadata": {"strength": strength, "reconstruction_divergence": group["reconstruction_divergence"]},
                }
            )
    return rows


def run_grouped_clt_analysis(manifest_path: str | Path, output_dir: str | Path | None = None) -> Path:
    manifest_file = Path(manifest_path)
    manifest = load_manifest(manifest_file)
    trace_id = manifest["trace_id"]
    root = Path(output_dir) if output_dir is not None else manifest_file.parent
    artifact_by_type = {artifact["artifact_type"]: artifact for artifact in manifest["artifacts"]}
    codes_path = manifest_file.parent / artifact_by_type["blt_codes"]["path"]
    graph_ir = json.loads((manifest_file.parent / artifact_by_type["mair_graph_ir"]["path"]).read_text(encoding="utf-8"))
    rows = _read_blt_codes(codes_path)
    bundle = fit_grouped_clt_rows(rows, trace_id, graph_ir["model_family"], graph_ir["model_variant"])
    grouped_path = root / "grouped_clt_bundle.v1.json"
    grouped_path.write_text(json.dumps(bundle, indent=2, sort_keys=True), encoding="utf-8")
    sweep_path = root / "intervention_sweep.v1.jsonl"
    with sweep_path.open("w", encoding="utf-8") as handle:
        for row in build_intervention_sweep(bundle):
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return write_manifest(root, trace_id=trace_id, producer="blt:analysis:0.1.0")
