from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mair.manifest import write_manifest
from mair.validate import validate_artifact, validate_manifest


def _write_artifacts(root: Path) -> None:
    (root / "mair_graph_ir.v1.json").write_text(
        json.dumps(
            {
                "trace_id": "trace-1",
                "model_family": "qwen3.5-hybrid",
                "model_variant": "mock-2b",
                "nodes": [{"id": "block-0:pre_d1", "kind": "pre_d1"}],
                "edges": [{"source": "block-0:pre_d1", "target": "block-0:block_output", "edge_class": "tract_update", "weight": 1.0}],
            }
        ),
        encoding="utf-8",
    )
    (root / "mair_numeric_lowering.v1.json").write_text(
        json.dumps(
            {
                "trace_id": "trace-1",
                "backend": "qwen3.5-hybrid",
                "recurrence_kernel": "chunked-deltanet",
                "bridge_realization": "attention",
                "precision": "fp32",
                "fused_kernels": False,
                "equivalence_witness": "abc123",
            }
        ),
        encoding="utf-8",
    )
    (root / "topology_summary.v1.json").write_text(
        json.dumps(
            {
                "trace_id": "trace-1",
                "topology_backend": "sketch",
                "scope": "trace",
                "bridge_policy": "bridge-aware",
                "intervention_axis": "code_group",
                "summary_metrics": {"component_count": 1},
            }
        ),
        encoding="utf-8",
    )
    with (root / "mair_semantic_trace.v1.jsonl").open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "op": "StateInit",
            "trace_id": "trace-1",
            "model_family": "qwen3.5-hybrid",
            "model_variant": "mock-2b",
            "block_id": "block-0",
            "token_span": [0, 0],
            "source_artifact_id": "src-1",
            "determinism_context": {"seed": "stable"},
            "payload": {"state_norm": 1.0},
        }) + "\n")
    with (root / "intervention_sweep.v1.jsonl").open("w", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "trace_id": "trace-1",
            "group_id": "g0",
            "intervention": "attenuate",
            "metric": "bridge_dependence",
            "delta": -0.1,
            "metadata": {"strength": 0.25},
        }) + "\n")
    (root / "grouped_clt_bundle.v1.json").write_text(
        json.dumps(
            {
                "trace_id": "trace-1",
                "model_family": "qwen3.5-hybrid",
                "model_variant": "mock-2b",
                "groups": [{"group_id": "g0", "size": 2, "reconstruction_divergence": 0.11, "bridge_dependence": 0.3, "centroid": [0.1, 0.2]}],
                "summary_metrics": {"mean_reconstruction_divergence": 0.11},
            }
        ),
        encoding="utf-8",
    )
    (root / "assurance_receipt.v1.json").write_text(
        json.dumps(
            {
                "trace_id": "trace-1",
                "decision": "allow_with_review",
                "gates": {"trace_completeness": True},
                "falsifiers": {"replay_determinism": False},
                "artifact_inputs": [{"artifact_type": "mair_graph_ir", "artifact_id": "id-1"}],
                "summary": {"status": "ok"},
            }
        ),
        encoding="utf-8",
    )
    pq.write_table(
        pa.table(
            {
                "trace_id": ["trace-1"],
                "token_index": [0],
                "block_id": ["block-0"],
                "code_group": ["g0"],
                "reconstruction_error": [0.1],
                "bridge_strength": [0.2],
            }
        ),
        root / "blt_codes.v1.parquet",
    )
    pq.write_table(
        pa.table(
            {
                "trace_id": ["trace-1"],
                "token_index": [0],
                "block_id": ["block-0"],
                "stage": ["post_d1"],
                "state_mean": [0.3],
                "state_norm": [1.2],
                "bridge_strength": [0.2],
                "gate_strength": [0.4],
            }
        ),
        root / "tract_state_snapshot.v1.parquet",
    )


def test_validate_artifact_roundtrip(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)
    validate_artifact(tmp_path / "mair_graph_ir.v1.json")
    validate_artifact(tmp_path / "blt_codes.v1.parquet")
    validate_artifact(tmp_path / "mair_semantic_trace.v1.jsonl")


def test_validate_manifest_walks_all_artifacts(tmp_path: Path) -> None:
    _write_artifacts(tmp_path)
    manifest_path = write_manifest(tmp_path, trace_id="trace-1", producer="mair:test:0.1.0")
    payload = validate_manifest(manifest_path)
    assert payload["trace_id"] == "trace-1"
    assert len(payload["artifacts"]) == 9
