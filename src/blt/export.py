from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from ._mair import ensure_mair_importable
from .capture import build_trace
from .extract import (
    build_blt_code_rows,
    build_graph_ir,
    build_numeric_lowering,
    build_semantic_trace,
    build_tract_state_rows,
)
from .topology import build_topology_summary
from .codes import run_grouped_clt_analysis
from .integrations.hybrid_mechlab import write_hybrid_mechlab_record

ensure_mair_importable()
from mair.manifest import write_manifest  # noqa: E402


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _write_parquet(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty parquet artifact: {path}")
    columns = {key: [row[key] for row in rows] for key in rows[0]}
    pq.write_table(pa.table(columns), path)


def run_trace(
    prompt: str,
    trace_id: str,
    output_dir: str | Path,
    *,
    backend: str = "mock",
    profile: str | Path | dict[str, Any] | None = None,
    model_family: str | None = None,
    model_variant: str | None = None,
    producer: str = "blt:trace:0.1.0",
) -> Path:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    trace = build_trace(
        prompt,
        trace_id,
        backend=backend,
        profile=profile,
        model_family=model_family,
        model_variant=model_variant,
    )
    _write_jsonl(root / "mair_semantic_trace.v1.jsonl", build_semantic_trace(trace))
    _write_json(root / "mair_graph_ir.v1.json", build_graph_ir(trace))
    _write_json(root / "mair_numeric_lowering.v1.json", build_numeric_lowering(trace))
    blt_rows = build_blt_code_rows(trace)
    _write_parquet(root / "blt_codes.v1.parquet", blt_rows)
    _write_parquet(root / "tract_state_snapshot.v1.parquet", build_tract_state_rows(trace))
    _write_json(root / "topology_summary.v1.json", build_topology_summary(trace, blt_rows))
    return write_manifest(root, trace_id=trace_id, producer=producer)


def run_analysis(manifest_path: str | Path, output_dir: str | Path | None = None) -> Path:
    return run_grouped_clt_analysis(manifest_path, output_dir=output_dir)


def export_hybrid_mechlab_trace(
    manifest_path: str | Path,
    output_path: str | Path | None = None,
) -> Path:
    return write_hybrid_mechlab_record(manifest_path, output_path=output_path)
