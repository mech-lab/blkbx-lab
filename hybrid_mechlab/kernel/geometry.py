"""Experimental discrete geometry helpers for research-only holonom risk."""

from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush

from hybrid_mechlab.kernel.graph import Graph


@dataclass(frozen=True)
class GeodesicSegment:
    start_node: int
    end_node: int
    cost: float
    edge_kind: str

    def to_record(self) -> dict[str, int | float | str]:
        return {
            "start_node": self.start_node,
            "end_node": self.end_node,
            "cost": self.cost,
            "edge_kind": self.edge_kind,
        }


@dataclass(frozen=True)
class GeodesicPath:
    start_node: int
    end_node: int
    node_ids: tuple[int, ...]
    segments: tuple[GeodesicSegment, ...]
    direct_span: int
    total_cost: float
    bridge_segments: int
    shortcut_gain: float
    curvature_proxy: float

    def to_record(self) -> dict[str, int | float | list[int] | list[dict[str, int | float | str]]]:
        return {
            "start_node": self.start_node,
            "end_node": self.end_node,
            "node_ids": list(self.node_ids),
            "segments": [segment.to_record() for segment in self.segments],
            "direct_span": self.direct_span,
            "total_cost": self.total_cost,
            "bridge_segments": self.bridge_segments,
            "shortcut_gain": self.shortcut_gain,
            "curvature_proxy": self.curvature_proxy,
        }


@dataclass(frozen=True)
class Holonom:
    value: float
    unit: str = "holonom"

    def to_record(self) -> dict[str, float | str]:
        return {"value": self.value, "unit": self.unit}


@dataclass(frozen=True)
class HolonomRisk:
    holonom: Holonom
    geodesic: GeodesicPath
    bridge_dependence: float
    tract_retention: float
    gluing_defect: float
    family: str
    backend: str

    def to_record(self) -> dict[str, object]:
        return {
            "holonom": self.holonom.to_record(),
            "geodesic": self.geodesic.to_record(),
            "bridge_dependence": self.bridge_dependence,
            "tract_retention": self.tract_retention,
            "gluing_defect": self.gluing_defect,
            "family": self.family,
            "backend": self.backend,
        }


def discrete_geodesic(
    graph: Graph,
    *,
    path_edges: list[tuple[int, int]] | tuple[tuple[int, int], ...] = (),
    bridge_edges: set[tuple[int, int]] | tuple[tuple[int, int], ...] = (),
    start_node: int | None = None,
    end_node: int | None = None,
    bridge_penalty: float = 0.35,
    closure_penalty: float = 0.15,
) -> GeodesicPath:
    node_ids = [int(node) for node in graph.nodes.tolist()]
    if not node_ids:
        raise ValueError("graph must contain at least one node")

    start = node_ids[0] if start_node is None else start_node
    end = node_ids[-1] if end_node is None else end_node
    if start not in node_ids or end not in node_ids:
        raise ValueError("start_node and end_node must both be present in the graph")

    path_set = {_normalize_edge(edge) for edge in path_edges}
    bridge_set = {_normalize_edge(edge) for edge in bridge_edges}
    adjacency: dict[int, list[tuple[int, float, str]]] = {node: [] for node in node_ids}
    for edge in graph.edge_tuples():
        left, right = _normalize_edge(edge)
        edge_kind = _edge_kind((left, right), path_set=path_set, bridge_set=bridge_set)
        edge_cost = _edge_cost(edge_kind, bridge_penalty=bridge_penalty, closure_penalty=closure_penalty)
        adjacency[left].append((right, edge_cost, edge_kind))
        adjacency[right].append((left, edge_cost, edge_kind))

    distances: dict[int, float] = {start: 0.0}
    previous: dict[int, tuple[int, float, str]] = {}
    queue: list[tuple[float, int]] = [(0.0, start)]
    while queue:
        distance, node = heappop(queue)
        if distance > distances.get(node, float("inf")):
            continue
        if node == end:
            break
        for neighbor, edge_cost, edge_kind in adjacency[node]:
            candidate = distance + edge_cost
            if candidate < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate
                previous[neighbor] = (node, edge_cost, edge_kind)
                heappush(queue, (candidate, neighbor))

    if end not in distances:
        raise ValueError("graph geodesic could not connect the selected nodes")

    ordered_nodes = [end]
    segments: list[GeodesicSegment] = []
    current = end
    while current != start:
        parent, edge_cost, edge_kind = previous[current]
        segments.append(
            GeodesicSegment(
                start_node=parent,
                end_node=current,
                cost=round(float(edge_cost), 6),
                edge_kind=edge_kind,
            )
        )
        ordered_nodes.append(parent)
        current = parent

    ordered_nodes.reverse()
    segments.reverse()
    direct_span = abs(end - start)
    total_cost = round(float(distances[end]), 6)
    bridge_segment_count = sum(1 for segment in segments if segment.edge_kind == "bridge")
    shortcut_gain = round(max(float(direct_span) - total_cost, 0.0), 6)
    curvature_proxy = round(max(total_cost - float(direct_span), 0.0), 6)
    return GeodesicPath(
        start_node=start,
        end_node=end,
        node_ids=tuple(ordered_nodes),
        segments=tuple(segments),
        direct_span=direct_span,
        total_cost=total_cost,
        bridge_segments=bridge_segment_count,
        shortcut_gain=shortcut_gain,
        curvature_proxy=curvature_proxy,
    )


def actuarial_holonom(
    geodesic: GeodesicPath,
    *,
    bridge_dependence: float,
    tract_retention: float,
    gluing_defect: float,
    family: str,
    backend: str,
) -> HolonomRisk:
    segment_count = max(len(geodesic.segments), 1)
    bridge_ratio = geodesic.bridge_segments / segment_count
    route_complexity = geodesic.total_cost + geodesic.shortcut_gain + geodesic.curvature_proxy
    risk_load = route_complexity * (1.0 + bridge_ratio + bridge_dependence + gluing_defect)
    stabilized_retention = max(tract_retention, 0.05)
    holonom_value = round(risk_load / stabilized_retention, 6)
    return HolonomRisk(
        holonom=Holonom(value=holonom_value),
        geodesic=geodesic,
        bridge_dependence=round(float(bridge_dependence), 6),
        tract_retention=round(float(tract_retention), 6),
        gluing_defect=round(float(gluing_defect), 6),
        family=family,
        backend=backend,
    )


def _edge_kind(
    edge: tuple[int, int],
    *,
    path_set: set[tuple[int, int]],
    bridge_set: set[tuple[int, int]],
) -> str:
    if edge in bridge_set:
        return "bridge"
    if edge in path_set:
        return "path"
    return "closure"


def _edge_cost(edge_kind: str, *, bridge_penalty: float, closure_penalty: float) -> float:
    if edge_kind == "bridge":
        return 1.0 + bridge_penalty
    if edge_kind == "closure":
        return 1.0 + closure_penalty
    return 1.0


def _normalize_edge(edge: tuple[int, int]) -> tuple[int, int]:
    left, right = edge
    return (left, right) if left <= right else (right, left)
