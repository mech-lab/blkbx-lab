"""Offline persistence reports and JSON artifact helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hybrid_mechlab.api import TraceHandle, backend_name
from hybrid_mechlab.io import jsonl
from hybrid_mechlab.kernel.graph import Graph
from hybrid_mechlab.kernel.persistence import (
    PersistenceComparison,
    PersistenceInput,
    PersistenceReport,
    build_summary,
    compare_reports,
    compute_exact_persistence,
)
from hybrid_mechlab.kernel.topology import (
    build_trace_complex,
    build_trace_graph,
    edge_filtration,
    vertex_filtration,
)
from hybrid_mechlab.topology.sheaf import build_partial_sheaf

ExactPersistenceInput = PersistenceInput


def compute_persistence(trace: TraceHandle) -> PersistenceReport:
    persistence_input = _build_persistence_input(trace)
    gluing_report = build_partial_sheaf(trace, basis="block_supernodes").gluing_report()
    diagrams = compute_exact_persistence(
        persistence_input,
        gluing_defect=gluing_report.defect_score,
        math_backend=trace.math_backend,
    )
    summary = build_summary(diagrams, persistence_input, gluing_defect=gluing_report.defect_score)
    return PersistenceReport(
        trace_id=trace.trace_id,
        profile_name=trace.profile.name,
        family=trace.profile.family.kind.value,
        backend=backend_name(trace.backend),
        persistence_input=persistence_input,
        diagrams=diagrams,
        summary=summary,
    )


def compare_persistence(
    left: TraceHandle | PersistenceReport,
    right: TraceHandle | PersistenceReport,
) -> PersistenceComparison:
    left_report = compute_persistence(left) if isinstance(left, TraceHandle) else left
    right_report = compute_persistence(right) if isinstance(right, TraceHandle) else right
    return compare_reports(left_report, right_report)


def export_persistence_report(report: PersistenceReport, path: str) -> str:
    return jsonl.save(path, report.to_record())


def export_persistence_comparison(comparison: PersistenceComparison, path: str) -> str:
    return jsonl.save(path, comparison.to_record())


def export_trace_and_persistence_artifacts(
    trace: TraceHandle,
    directory: str,
) -> dict[str, str]:
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    trace_path = target / f"{trace.trace_id}.trace.json"
    persistence_path = target / f"{trace.trace_id}.persistence.json"
    jsonl.save(str(trace_path), trace.to_record())
    report = compute_persistence(trace)
    jsonl.save(str(persistence_path), report.to_record())
    return {"trace": str(trace_path), "persistence": str(persistence_path)}


def report_to_topology_summary_record(
    report: PersistenceReport,
    *,
    artifact_refs: list[str] | None = None,
) -> dict[str, Any]:
    summary = report.summary
    return {
        "trace_id": report.trace_id,
        "topology_backend": "exact_persistence",
        "scope": "trace",
        "bridge_policy": "bridge-aware",
        "intervention_axis": "code_group",
        "summary_metrics": {
            "h0_pairs": summary.h0_pairs,
            "h1_pairs": summary.h1_pairs,
            "infinite_pairs": summary.infinite_pairs,
            "max_finite_persistence": summary.max_finite_persistence,
            "total_finite_persistence": summary.total_finite_persistence,
            "topological_susceptibility": summary.topology_drift,
        },
        "gluing_defect": summary.gluing_defect,
        "bridge_dependence": summary.bridge_dependence,
        "tract_retention": summary.tract_retention,
        "artifact_refs": list(artifact_refs or []),
    }


def report_to_offline_topology_record(
    report: PersistenceReport,
    *,
    artifact_refs: list[str] | None = None,
) -> dict[str, Any]:
    summary = report.summary
    return {
        "trace_id": report.trace_id,
        "family": report.family,
        "backend": report.backend,
        "profile_name": report.profile_name,
        "summary": {
            "gluing_defect": summary.gluing_defect,
            "bridge_dependence": summary.bridge_dependence,
            "tract_retention": summary.tract_retention,
            "topological_susceptibility": summary.topology_drift,
            "h0_pairs": summary.h0_pairs,
            "h1_pairs": summary.h1_pairs,
            "infinite_pairs": summary.infinite_pairs,
            "max_finite_persistence": summary.max_finite_persistence,
            "total_finite_persistence": summary.total_finite_persistence,
        },
        "diagrams": [
            {
                "homology_degree": diagram.dimension,
                "pairs": [{"birth": pair.birth, "death": pair.death} for pair in diagram.pairs],
            }
            for diagram in report.diagrams
        ],
        "artifact_refs": list(artifact_refs or []),
    }


def export_mair_topology_artifacts(
    trace: TraceHandle | PersistenceReport,
    directory: str,
) -> dict[str, str]:
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    report = compute_persistence(trace) if isinstance(trace, TraceHandle) else trace
    topology_summary_path = target / "topology_summary.v1.json"
    offline_report_path = target / "offline_topology_report.v1.json"
    jsonl.save(
        str(topology_summary_path),
        report_to_topology_summary_record(report, artifact_refs=[offline_report_path.name]),
    )
    jsonl.save(
        str(offline_report_path),
        report_to_offline_topology_record(report, artifact_refs=[topology_summary_path.name]),
    )
    return {
        "topology_summary": str(topology_summary_path),
        "offline_topology_report": str(offline_report_path),
    }


def _build_persistence_input(trace: TraceHandle) -> ExactPersistenceInput:
    graph, path_edges, bridge_edges = trace_graph_inputs(trace)
    complex_ = build_trace_complex(graph)
    vertex_values = vertex_filtration(len(graph.nodes), trace.transport_digest.retention_score)
    edge_values = edge_filtration(
        graph.edge_tuples(),
        path_edges,
        bridge_edges,
        local_steps=trace.transport_digest.local_steps,
        bridge_crossings=trace.transport_digest.bridge_crossings,
        retention_score=trace.transport_digest.retention_score,
        cancellation_pairs=trace.signed_sketch.cancellation_pairs,
        vertex_values=vertex_values,
    )
    return ExactPersistenceInput(
        trace_id=trace.trace_id,
        family=trace.profile.family.kind.value,
        backend=backend_name(trace.backend),
        graph=graph,
        complex=complex_,
        vertex_filtration=vertex_values,
        edge_filtration=edge_values,
        local_steps=trace.transport_digest.local_steps,
        bridge_crossings=trace.transport_digest.bridge_crossings,
        retention_score=trace.transport_digest.retention_score,
        signed_sketch=trace._signed_sketch(),  # type: ignore[attr-defined]
    )


def trace_graph_inputs(trace: TraceHandle) -> tuple[Graph, list[tuple[int, int]], set[tuple[int, int]]]:
    graph_ir = trace.profile.metadata.get("mair_graph_ir")
    if isinstance(graph_ir, dict):
        nodes = graph_ir.get("nodes", [])
        edges = graph_ir.get("edges", [])
        node_positions = {
            str(node["id"]): idx
            for idx, node in enumerate(nodes)
            if isinstance(node, dict) and node.get("id") is not None
        }
        edge_list: list[tuple[int, int]] = []
        path_edges: list[tuple[int, int]] = []
        bridge_edges: set[tuple[int, int]] = set()
        for edge in edges:
            if not isinstance(edge, dict):
                continue
            source = node_positions.get(str(edge.get("source")))
            target = node_positions.get(str(edge.get("target")))
            if source is None or target is None:
                continue
            pair = (source, target)
            edge_list.append(pair)
            if edge.get("edge_class") == "bridge_flow":
                bridge_edges.add(pair)
            else:
                path_edges.append(pair)
        if edge_list:
            return Graph(nodes=tuple(range(len(node_positions))), edges=edge_list), path_edges, bridge_edges

    graph, path_edges, bridge_edges = build_trace_graph(
        trace.schedule,
        cancellation_pairs=trace.signed_sketch.cancellation_pairs,
    )
    return graph, path_edges, bridge_edges
