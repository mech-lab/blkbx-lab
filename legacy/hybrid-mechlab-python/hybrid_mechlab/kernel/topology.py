"""Graph and filtration builders for trace-derived topology."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from hybrid_mechlab.kernel.array import as_float_array
from hybrid_mechlab.kernel.graph import Graph
from hybrid_mechlab.kernel.simplicial import SimplicialComplex, Simplex
from hybrid_mechlab.schedules import HybridSchedule, TransportRegimeKind


@dataclass(frozen=True)
class SignedSketch:
    positive_components: int
    negative_components: int
    cancellation_pairs: int
    cycle_hint: int

    def to_record(self) -> dict[str, int]:
        return {
            "positive_components": self.positive_components,
            "negative_components": self.negative_components,
            "cancellation_pairs": self.cancellation_pairs,
            "cycle_hint": self.cycle_hint,
        }


def signed_sketch_from_counts(
    *,
    positive_components: int,
    negative_components: int,
    cancellation_pairs: int,
    cycle_hint: int,
) -> SignedSketch:
    return SignedSketch(
        positive_components=positive_components,
        negative_components=negative_components,
        cancellation_pairs=cancellation_pairs,
        cycle_hint=cycle_hint,
    )


def build_trace_graph(
    schedule: HybridSchedule,
    *,
    cancellation_pairs: int,
) -> tuple[Graph, list[tuple[int, int]], set[tuple[int, int]]]:
    node_ids = tuple(range(len(schedule.ops) + 1))
    last_node = node_ids[-1]
    path_edges = [(idx, idx + 1) for idx in range(last_node)]
    bridge_edges = {
        (0, op.local_index + 1)
        for op in schedule.ops
        if op.kind == TransportRegimeKind.global_bridge and op.local_index + 1 < len(node_ids)
    }
    cancellation_edges = []
    if cancellation_pairs > 0 and last_node >= 3:
        cancellation_edges.append((1, last_node))
    edge_list = sorted(set(path_edges + list(bridge_edges) + cancellation_edges))
    return Graph(nodes=node_ids, edges=edge_list), path_edges, bridge_edges


def build_trace_complex(graph: Graph) -> SimplicialComplex:
    simplices = [Simplex(vertices=(int(node),)) for node in graph.nodes.tolist()]
    simplices.extend(
        Simplex(vertices=(int(left), int(right))) for left, right in graph.edge_tuples()
    )
    return SimplicialComplex(tuple(simplices))


def vertex_filtration(node_count: int, retention_score: float) -> np.ndarray:
    denom = node_count + 1
    scale = 1.0 - (retention_score * 0.15)
    return as_float_array(round(((idx + 1) / denom) * scale, 6) for idx in range(node_count))


def edge_filtration(
    edge_list: tuple[tuple[int, int], ...] | list[tuple[int, int]],
    path_edges: list[tuple[int, int]],
    bridge_edges: set[tuple[int, int]],
    *,
    local_steps: int,
    bridge_crossings: int,
    retention_score: float,
    cancellation_pairs: int = 0,
    vertex_values: np.ndarray,
) -> np.ndarray:
    denom = max(len(edge_list) + 1, 1)
    bridge_dependence = bridge_crossings / max(local_steps + bridge_crossings, 1)
    values: list[float] = []
    for idx, edge in enumerate(edge_list):
        left, right = edge
        vertex_max = max(float(vertex_values[left]), float(vertex_values[right]))
        if edge in bridge_edges:
            offset = 0.1 + (bridge_dependence * 0.1)
        elif edge in path_edges:
            offset = 0.03 + (retention_score * 0.03)
        else:
            offset = 0.12 + (cancellation_pairs * 0.01)
        step = (idx + 1) / denom
        values.append(round(vertex_max + offset + step * 0.02, 6))
    return as_float_array(values)
