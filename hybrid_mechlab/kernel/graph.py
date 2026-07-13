"""Graph primitives for offline topology."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from hybrid_mechlab.kernel.array import as_edge_array, as_int_array


@dataclass(frozen=True, init=False)
class Graph:
    nodes: np.ndarray
    edges: np.ndarray

    def __init__(
        self,
        nodes: Iterable[int] | np.ndarray,
        edges: Iterable[tuple[int, int]] | np.ndarray,
    ) -> None:
        object.__setattr__(self, "nodes", as_int_array(nodes).reshape(-1))
        object.__setattr__(self, "edges", as_edge_array(edges))

    def edge_tuples(self) -> tuple[tuple[int, int], ...]:
        return tuple((int(left), int(right)) for left, right in self.edges.tolist())

    def to_record(self) -> dict[str, list[int] | list[list[int]]]:
        return {
            "nodes": [int(node) for node in self.nodes.tolist()],
            "edges": [[int(left), int(right)] for left, right in self.edges.tolist()],
        }
