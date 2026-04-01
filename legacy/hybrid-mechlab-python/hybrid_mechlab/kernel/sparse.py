"""Sparse vector and batch containers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

import numpy as np

from hybrid_mechlab.kernel.array import as_float_array, as_int_array


@dataclass(frozen=True)
class SparseVector:
    ids: np.ndarray
    values: np.ndarray

    def __post_init__(self) -> None:
        ids = as_int_array(self.ids).reshape(-1)
        values = as_float_array(self.values).reshape(-1)
        if ids.shape != values.shape:
            raise ValueError("ids and values must have the same shape")
        object.__setattr__(self, "ids", ids)
        object.__setattr__(self, "values", values)

    @classmethod
    def from_pairs(cls, pairs: Iterable[tuple[int, float]]) -> "SparseVector":
        pair_tuple = tuple(pairs)
        ids, values = zip(*pair_tuple) if pair_tuple else (tuple(), tuple())
        return cls(ids=ids, values=values)

    @property
    def nnz(self) -> int:
        return int(self.ids.size)

    def is_nonempty(self) -> bool:
        return bool(self.nnz)

    def to_record(self) -> dict[str, list[int] | list[float]]:
        return {
            "feature_ids": [int(item) for item in self.ids.tolist()],
            "feature_values": [round(float(item), 6) for item in self.values.tolist()],
        }


@dataclass(frozen=True)
class SparseBatch:
    vectors: tuple[SparseVector, ...]

    @classmethod
    def from_rows(
        cls,
        rows: Iterable[tuple[Sequence[int], Sequence[float]]],
    ) -> "SparseBatch":
        return cls(
            tuple(SparseVector(ids=ids, values=values) for ids, values in rows)
        )

    @property
    def nnz(self) -> int:
        return int(sum(vector.nnz for vector in self.vectors))

    def is_nonempty(self) -> bool:
        return any(vector.is_nonempty() for vector in self.vectors)

    def to_trace_records(self, hooks: Sequence[str]) -> tuple[dict[str, Any], ...]:
        records: list[dict[str, Any]] = []
        for idx, vector in enumerate(self.vectors):
            hook = hooks[idx] if idx < len(hooks) else f"kernel.hook.{idx}"
            records.append({"hook": hook, **vector.to_record()})
        return tuple(records)
