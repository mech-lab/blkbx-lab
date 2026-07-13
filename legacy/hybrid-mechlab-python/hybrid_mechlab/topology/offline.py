"""Offline persistence reports and JSON artifact helpers."""

from __future__ import annotations

from pathlib import Path

from ..api import TraceHandle, backend_name
from ..io import jsonl
from ..kernel.graph import Graph
from ..kernel.persistence import (
    PersistenceComparison,
    PersistenceInput,
    PersistenceReport,
    build_summary,
    compare_reports,
    compute_exact_persistence,
)
from ..kernel.topology import (
    build_trace_complex,
    build_trace_graph,
    edge_filtration,
    vertex_filtration,
)
from .sheaf import build_partial_sheaf

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
    return build_trace_graph(
        trace.schedule,
        cancellation_pairs=trace.signed_sketch.cancellation_pairs,
    )
