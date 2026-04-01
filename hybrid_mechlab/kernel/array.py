"""Array normalization helpers for the NumPy math kernel."""

from __future__ import annotations

from typing import Iterable

import numpy as np


def as_float_array(values: Iterable[float]) -> np.ndarray:
    return np.asarray(tuple(values), dtype=np.float32)


def as_int_array(values: Iterable[int]) -> np.ndarray:
    return np.asarray(tuple(values), dtype=np.int64)


def as_edge_array(values: Iterable[tuple[int, int]]) -> np.ndarray:
    edges = np.asarray(tuple(values), dtype=np.int64)
    if edges.size == 0:
        return np.empty((0, 2), dtype=np.int64)
    return edges.reshape((-1, 2))
