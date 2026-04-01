from __future__ import annotations

from typing import Any


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _norm(values: list[float]) -> float:
    return round(sum(value * value for value in values) ** 0.5, 6)


def build_semantic_trace(trace: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for block in trace["blocks"]:
        block_id = block["block_id"]
        for token_record in block["token_records"]:
            token_index = token_record["token_index"]
            stages = token_record["stages"]
            determinism_context = {
                "trace_id": trace["trace_id"],
                "token": token_record["token"],
                "token_index": token_index,
            }
            rows.extend(
                [
                    {
                        "op": "StateRead",
                        "trace_id": trace["trace_id"],
                        "model_family": trace["model_family"],
                        "model_variant": trace["model_variant"],
                        "block_id": block_id,
                        "token_span": [token_index, token_index],
                        "source_artifact_id": f"{block_id}:pre_d1:{token_index}",
                        "determinism_context": determinism_context,
                        "payload": {
                            "stage": "pre_d1",
                            "state_mean": _mean(stages["pre_d1"]),
                            "state_norm": _norm(stages["pre_d1"]),
                        },
                    },
                    {
                        "op": "StateUpdate",
                        "trace_id": trace["trace_id"],
                        "model_family": trace["model_family"],
                        "model_variant": trace["model_variant"],
                        "block_id": block_id,
                        "token_span": [token_index, token_index],
                        "source_artifact_id": f"{block_id}:post_d3:{token_index}",
                        "determinism_context": determinism_context,
                        "payload": {
                            "stage": "post_d3",
                            "state_mean": _mean(stages["post_d3"]),
                            "state_norm": _norm(stages["post_d3"]),
                        },
                    },
                    {
                        "op": "BridgeApply",
                        "trace_id": trace["trace_id"],
                        "model_family": trace["model_family"],
                        "model_variant": trace["model_variant"],
                        "block_id": block_id,
                        "token_span": [token_index, token_index],
                        "source_artifact_id": f"{block_id}:post_attention:{token_index}",
                        "determinism_context": determinism_context,
                        "payload": {
                            "stage": "post_attention",
                            "bridge_strength": abs(_mean(stages["post_attention"])),
                            "bridge_norm": _norm(stages["post_attention"]),
                        },
                    },
                ]
            )
    return rows


def build_graph_ir(trace: dict[str, Any]) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    node_kinds = ["pre_d1", "post_d1", "post_d2", "post_d3", "post_attention", "block_output"]
    edge_classes = ["tract_update", "tract_update", "tract_update", "bridge_flow", "residual_flow"]
    for block in trace["blocks"]:
        block_id = block["block_id"]
        block_nodes = [f"{block_id}:{kind}" for kind in node_kinds]
        for node_id, kind in zip(block_nodes, node_kinds, strict=True):
            nodes.append({"id": node_id, "kind": kind, "block_id": block_id})
        for source, target, edge_class in zip(block_nodes[:-1], block_nodes[1:], edge_classes, strict=True):
            edges.append({"source": source, "target": target, "edge_class": edge_class, "weight": 1.0})
    return {
        "trace_id": trace["trace_id"],
        "model_family": trace["model_family"],
        "model_variant": trace["model_variant"],
        "capture_backend": trace.get("capture_backend", "mock"),
        "profile_id": trace.get("profile_id"),
        "nodes": nodes,
        "edges": edges,
    }


def build_numeric_lowering(trace: dict[str, Any]) -> dict[str, Any]:
    runtime = trace.get("runtime") or {}
    return {
        "trace_id": trace["trace_id"],
        "backend": trace.get("capture_backend", trace["model_family"]),
        "recurrence_kernel": "chunked-deltanet",
        "bridge_realization": "attention",
        "precision": runtime.get("dtype", "fp32"),
        "fused_kernels": False,
        "profile_id": trace.get("profile_id"),
        "equivalence_witness": f"{trace['trace_id']}-{len(trace['tokens'])}-{trace['block_count']}",
    }


def build_tract_state_rows(trace: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    tracked_stages = ("post_d1", "post_d2", "post_d3")
    for block in trace["blocks"]:
        for token_record in block["token_records"]:
            for stage in tracked_stages:
                values = token_record["stages"][stage]
                attention = token_record["stages"]["post_attention"]
                rows.append(
                    {
                        "trace_id": trace["trace_id"],
                        "token_index": token_record["token_index"],
                        "block_id": block["block_id"],
                        "stage": stage,
                        "state_mean": _mean(values),
                        "state_norm": _norm(values),
                        "bridge_strength": abs(_mean(attention)),
                        "gate_strength": abs(_mean(token_record["stages"]["post_d2"])),
                    }
                )
    return rows


def build_blt_code_rows(trace: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for block in trace["blocks"]:
        for token_record in block["token_records"]:
            post_d3 = token_record["stages"]["post_d3"]
            attention = token_record["stages"]["post_attention"]
            code_group = f"g{(token_record['token_index'] + int(block['block_id'].split('-')[-1])) % 3}"
            rows.append(
                {
                    "trace_id": trace["trace_id"],
                    "token_index": token_record["token_index"],
                    "block_id": block["block_id"],
                    "code_group": code_group,
                    "code_0": post_d3[0],
                    "code_1": post_d3[1],
                    "code_2": post_d3[2],
                    "code_3": post_d3[3],
                    "reconstruction_error": round(abs(_mean(post_d3) - _mean(attention)), 6),
                    "bridge_strength": abs(_mean(attention)),
                }
            )
    return rows
