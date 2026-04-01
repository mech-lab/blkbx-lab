"""Simplicial primitives for offline topology."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from hybrid_mechlab.kernel.array import as_int_array


@dataclass(frozen=True)
class Simplex:
    vertices: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "vertices", as_int_array(self.vertices).reshape(-1))

    def to_record(self) -> list[int]:
        return [int(vertex) for vertex in self.vertices.tolist()]


@dataclass(frozen=True)
class SimplicialComplex:
    simplices: tuple[Simplex, ...]

    @classmethod
    def from_iterable(cls, simplices: Iterable[Iterable[int]]) -> "SimplicialComplex":
        return cls(tuple(Simplex(vertices=tuple(simplex)) for simplex in simplices))

    def to_record(self) -> list[list[int]]:
        return [simplex.to_record() for simplex in self.simplices]
