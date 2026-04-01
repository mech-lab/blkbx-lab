from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def write_full_artifact_set(root: Path) -> None:
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
                "topology_backend": "exact_persistence",
                "scope": "trace",
                "bridge_policy": "bridge-aware",
                "intervention_axis": "code_group",
                "summary_metrics": {"component_count": 1},
                "gluing_defect": 0.125,
                "bridge_dependence": 0.3,
                "tract_retention": 0.7,
                "artifact_refs": ["offline_topology_report.v1.json"],
            }
        ),
        encoding="utf-8",
    )
    (root / "offline_topology_report.v1.json").write_text(
        json.dumps(
            {
                "trace_id": "trace-1",
                "family": "qwen3.5-hybrid",
                "backend": "qwen_hybrid_hf",
                "profile_name": "qwen3.5-2b-hybrid-v1",
                "summary": {
                    "gluing_defect": 0.125,
                    "bridge_dependence": 0.3,
                    "tract_retention": 0.7,
                    "topological_susceptibility": 0.11,
                },
                "diagrams": [
                    {
                        "homology_degree": 0,
                        "pairs": [
                            {"birth": 0.0, "death": 1.0},
                            {"birth": 0.2, "death": None},
                        ],
                    }
                ],
                "artifact_refs": ["topology_summary.v1.json"],
            }
        ),
        encoding="utf-8",
    )
    (root / "backend_comparison.v1.json").write_text(
        json.dumps(
            {
                "left_trace_id": "trace-1",
                "right_trace_id": "trace-2",
                "backend_pair": ["adapter", "qwen_hybrid_hf"],
                "schema_match": True,
                "bridge_dependence_delta": -0.05,
                "tract_retention_delta": 0.08,
                "topology_distance": 0.12,
                "notes": ["same profile, different backend"],
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
                "basis": "block_supernodes",
                "groups": [
                    {
                        "group_id": "g0",
                        "size": 2,
                        "reconstruction_divergence": 0.11,
                        "bridge_dependence": 0.3,
                        "centroid": [0.1, 0.2],
                        "lineage_ids": ["lin-0"],
                        "topology_metrics": {"gluing_defect": 0.125},
                    }
                ],
                "summary_metrics": {"mean_reconstruction_divergence": 0.11},
                "artifact_refs": ["concept_lineage_bundle.v1.json"],
            }
        ),
        encoding="utf-8",
    )
    (root / "concept_lineage_bundle.v1.json").write_text(
        json.dumps(
            {
                "trace_id": "trace-1",
                "basis": "block_supernodes",
                "groups": [{"group_id": "g0", "size": 2, "centroid": [0.1, 0.2]}],
                "lineages": [{"lineage_id": "lin-0", "members": ["g0"], "metrics": {"stability": 0.9}}],
                "summary_metrics": {"lineage_count": 1},
                "artifact_refs": ["grouped_clt_bundle.v1.json"],
            }
        ),
        encoding="utf-8",
    )
    (root / "replacement_eval.v1.json").write_text(
        json.dumps(
            {
                "trace_id": "trace-1",
                "replacement_scope": "block",
                "block_ids": ["block-0"],
                "logit_divergence": 0.04,
                "hidden_state_divergence": 0.02,
                "bridge_dependence_delta": -0.03,
                "topology_drift": 0.07,
                "metadata": {"mode": "centroid"},
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
                "summary": {"passed": ["trace_completeness"], "failed": [], "notes": ["fixture receipt"]},
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
