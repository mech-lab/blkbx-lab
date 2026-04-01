"""Exact persistence and report types for the NumPy math kernel."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, TYPE_CHECKING

import numpy as np

from hybrid_mechlab.kernel.array import as_float_array
from hybrid_mechlab.kernel.graph import Graph
from hybrid_mechlab.kernel.metrics import (
    bridge_dependence,
    topological_susceptibility,
    tract_retention,
)
from hybrid_mechlab.kernel.simplicial import SimplicialComplex
from hybrid_mechlab.kernel.topology import SignedSketch

if TYPE_CHECKING:
    from hybrid_mechlab.kernel.backend import MathKernelBackend


@dataclass(frozen=True)
class PersistenceInput:
    trace_id: str
    family: str
    backend: str
    graph: Graph
    complex: SimplicialComplex
    vertex_filtration: np.ndarray
    edge_filtration: np.ndarray
    local_steps: int
    bridge_crossings: int
    retention_score: float
    signed_sketch: SignedSketch

    def __post_init__(self) -> None:
        object.__setattr__(self, "vertex_filtration", as_float_array(self.vertex_filtration).reshape(-1))
        object.__setattr__(self, "edge_filtration", as_float_array(self.edge_filtration).reshape(-1))

    def to_record(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "family": self.family,
            "backend": self.backend,
            "node_ids": [int(node) for node in self.graph.nodes.tolist()],
            "edge_list": [[int(left), int(right)] for left, right in self.graph.edge_tuples()],
            "vertex_filtration": [round(float(value), 6) for value in self.vertex_filtration.tolist()],
            "edge_filtration": [round(float(value), 6) for value in self.edge_filtration.tolist()],
            "local_steps": self.local_steps,
            "bridge_crossings": self.bridge_crossings,
            "retention_score": self.retention_score,
            "signed_sketch": self.signed_sketch.to_record(),
        }


@dataclass(frozen=True)
class BirthDeathPair:
    dimension: int
    birth: float
    death: float | None

    @property
    def persistence(self) -> float | None:
        if self.death is None:
            return None
        return self.death - self.birth


@dataclass(frozen=True)
class PersistenceDiagram:
    dimension: int
    pairs: tuple[BirthDeathPair, ...]

    def finite_pairs(self) -> tuple[BirthDeathPair, ...]:
        return tuple(pair for pair in self.pairs if pair.death is not None)


@dataclass(frozen=True)
class PersistenceSummary:
    h0_pairs: int
    h1_pairs: int
    infinite_pairs: int
    max_finite_persistence: float
    total_finite_persistence: float
    bridge_dependence: float
    tract_retention: float
    topology_drift: float
    gluing_defect: float


@dataclass(frozen=True)
class PersistenceReport:
    trace_id: str
    profile_name: str
    family: str
    backend: str
    persistence_input: PersistenceInput
    diagrams: tuple[PersistenceDiagram, ...]
    summary: PersistenceSummary

    def to_record(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "profile_name": self.profile_name,
            "family": self.family,
            "backend": self.backend,
            "persistence_input": self.persistence_input.to_record(),
            "diagrams": [
                {
                    "dimension": diagram.dimension,
                    "pairs": [asdict(pair) for pair in diagram.pairs],
                }
                for diagram in self.diagrams
            ],
            "summary": asdict(self.summary),
        }


@dataclass(frozen=True)
class PersistenceComparison:
    left_trace_id: str
    right_trace_id: str
    backend_pair: tuple[str, str]
    family_pair: tuple[str, str]
    left_summary: PersistenceSummary
    right_summary: PersistenceSummary
    max_finite_persistence_delta: float
    total_finite_persistence_delta: float
    bridge_dependence_delta: float
    tract_retention_delta: float
    topology_drift_delta: float
    gluing_defect_delta: float

    def to_record(self) -> dict[str, Any]:
        return {
            "left_trace_id": self.left_trace_id,
            "right_trace_id": self.right_trace_id,
            "backend_pair": list(self.backend_pair),
            "family_pair": list(self.family_pair),
            "left_summary": asdict(self.left_summary),
            "right_summary": asdict(self.right_summary),
            "max_finite_persistence_delta": self.max_finite_persistence_delta,
            "total_finite_persistence_delta": self.total_finite_persistence_delta,
            "bridge_dependence_delta": self.bridge_dependence_delta,
            "tract_retention_delta": self.tract_retention_delta,
            "topology_drift_delta": self.topology_drift_delta,
            "gluing_defect_delta": self.gluing_defect_delta,
        }


class _UnionFind:
    def __init__(self, births: np.ndarray) -> None:
        self.parent = np.arange(births.size, dtype=np.int64)
        self.birth = births.astype(np.float32, copy=True)

    def find(self, idx: int) -> int:
        parent = int(self.parent[idx])
        if parent != idx:
            root = self.find(parent)
            self.parent[idx] = root
            return root
        return idx

    def union(self, left: int, right: int) -> tuple[float, float] | None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return None
        left_birth = float(self.birth[left_root])
        right_birth = float(self.birth[right_root])
        if left_birth <= right_birth:
            self.parent[right_root] = left_root
            self.birth[left_root] = min(left_birth, right_birth)
            return right_birth, left_birth
        self.parent[left_root] = right_root
        self.birth[right_root] = min(left_birth, right_birth)
        return left_birth, right_birth


def compute_exact_persistence(
    persistence_input: PersistenceInput,
    *,
    gluing_defect: float = 0.0,
    math_backend: str = "python",
) -> tuple[PersistenceDiagram, ...]:
    if math_backend != "python":
        raise RuntimeError("this repo is python-only; only math_backend='python' is supported")
    return _compute_exact_persistence_python(persistence_input)


def build_summary(
    diagrams: tuple[PersistenceDiagram, ...],
    persistence_input: PersistenceInput,
    *,
    gluing_defect: float = 0.0,
) -> PersistenceSummary:
    all_pairs = tuple(pair for diagram in diagrams for pair in diagram.pairs)
    finite_pairs = tuple(pair for pair in all_pairs if pair.death is not None)
    max_persistence = max((pair.persistence or 0.0) for pair in finite_pairs) if finite_pairs else 0.0
    total_persistence = sum((pair.persistence or 0.0) for pair in finite_pairs)
    sketch = persistence_input.signed_sketch
    return PersistenceSummary(
        h0_pairs=len(diagrams[0].pairs) if diagrams else 0,
        h1_pairs=len(diagrams[1].pairs) if len(diagrams) > 1 else 0,
        infinite_pairs=sum(1 for pair in all_pairs if pair.death is None),
        max_finite_persistence=round(float(max_persistence), 6),
        total_finite_persistence=round(float(total_persistence), 6),
        bridge_dependence=round(
            float(bridge_dependence(persistence_input.local_steps, persistence_input.bridge_crossings)),
            6,
        ),
        tract_retention=round(float(tract_retention(persistence_input.retention_score)), 6),
        topology_drift=round(
            float(
                topological_susceptibility(
                    sketch.positive_components,
                    sketch.negative_components,
                    sketch.cancellation_pairs,
                )
            ),
            6,
        ),
        gluing_defect=round(float(gluing_defect), 6),
    )


def compare_reports(left: PersistenceReport, right: PersistenceReport) -> PersistenceComparison:
    return PersistenceComparison(
        left_trace_id=left.trace_id,
        right_trace_id=right.trace_id,
        backend_pair=(left.backend, right.backend),
        family_pair=(left.family, right.family),
        left_summary=left.summary,
        right_summary=right.summary,
        max_finite_persistence_delta=round(
            left.summary.max_finite_persistence - right.summary.max_finite_persistence,
            6,
        ),
        total_finite_persistence_delta=round(
            left.summary.total_finite_persistence - right.summary.total_finite_persistence,
            6,
        ),
        bridge_dependence_delta=round(
            left.summary.bridge_dependence - right.summary.bridge_dependence,
            6,
        ),
        tract_retention_delta=round(
            left.summary.tract_retention - right.summary.tract_retention,
            6,
        ),
        topology_drift_delta=round(
            left.summary.topology_drift - right.summary.topology_drift,
            6,
        ),
        gluing_defect_delta=round(
            left.summary.gluing_defect - right.summary.gluing_defect,
            6,
        ),
    )


def _compute_exact_persistence_python(
    persistence_input: PersistenceInput,
) -> tuple[PersistenceDiagram, ...]:
    nodes = _normalized_nodes(persistence_input)
    vertex_filtration = _normalized_vertex_filtration(nodes, persistence_input.vertex_filtration)
    node_positions = {node: idx for idx, node in enumerate(nodes)}
    edge_entries = _normalized_edges(persistence_input, node_positions, vertex_filtration)
    union_find = _UnionFind(vertex_filtration)
    h0_pairs: list[BirthDeathPair] = []
    h1_pairs: list[BirthDeathPair] = []

    for left, right, filtration in edge_entries:
        event = union_find.union(left, right)
        if event is None:
            h1_pairs.append(BirthDeathPair(dimension=1, birth=filtration, death=None))
            continue
        birth, _survivor_birth = event
        h0_pairs.append(BirthDeathPair(dimension=0, birth=birth, death=filtration))

    roots = {union_find.find(idx) for idx in range(len(nodes))}
    for root in sorted(roots):
        h0_pairs.append(
            BirthDeathPair(
                dimension=0,
                birth=round(float(union_find.birth[root]), 6),
                death=None,
            )
        )

    h0_pairs.sort(key=_pair_sort_key)
    h1_pairs.sort(key=_pair_sort_key)
    return (
        PersistenceDiagram(dimension=0, pairs=tuple(h0_pairs)),
        PersistenceDiagram(dimension=1, pairs=tuple(h1_pairs)),
    )


def _normalized_nodes(persistence_input: PersistenceInput) -> list[int]:
    nodes = [int(node) for node in persistence_input.graph.nodes.tolist()]
    if not nodes:
        for left, right in persistence_input.graph.edge_tuples():
            nodes.extend((left, right))
    if not nodes and persistence_input.vertex_filtration.size:
        nodes.extend(range(int(persistence_input.vertex_filtration.size)))
    if not nodes:
        nodes.append(0)
    return sorted(set(nodes))


def _normalized_vertex_filtration(nodes: list[int], provided: np.ndarray) -> np.ndarray:
    if provided.size == len(nodes):
        return provided.astype(np.float32, copy=True)
    denom = len(nodes) + 1
    return as_float_array((idx + 1) / denom for idx in range(len(nodes)))


def _normalized_edges(
    persistence_input: PersistenceInput,
    node_positions: dict[int, int],
    vertex_filtration: np.ndarray,
) -> list[tuple[int, int, float]]:
    edges = sorted(set(persistence_input.graph.edge_tuples()))
    if persistence_input.edge_filtration.size == len(edges):
        edge_weights = persistence_input.edge_filtration.astype(np.float32, copy=True)
    else:
        denom = len(edges) + 1
        edge_weights = as_float_array(
            max(vertex_filtration[node_positions[left]], vertex_filtration[node_positions[right]])
            + ((idx + 1) / denom)
            for idx, (left, right) in enumerate(edges)
        )

    entries: list[tuple[int, int, float]] = []
    for idx, (left, right) in enumerate(edges):
        left_idx = node_positions.get(left, 0)
        right_idx = node_positions.get(right, 0)
        filtration = max(
            float(edge_weights[idx]),
            float(vertex_filtration[left_idx]),
            float(vertex_filtration[right_idx]),
        )
        entries.append((left_idx, right_idx, round(float(filtration), 6)))
    entries.sort(key=lambda item: (item[2], item[0], item[1]))
    return entries


def _pair_sort_key(pair: BirthDeathPair) -> tuple[float, float, int]:
    death_value = float(pair.death) if pair.death is not None else float("inf")
    death_rank = 1 if pair.death is None else 0
    return (float(pair.birth), death_value, death_rank)
