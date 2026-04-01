"""Internal lazy shim around the optional hm_pyo3 extension module."""

from __future__ import annotations

import importlib
import importlib.util
from types import ModuleType

MISSING_RUST_MESSAGE = (
    "math_backend='rust' requires the optional hybrid-mechlab-rust companion package"
)

_MODULE: ModuleType | None = None


def available() -> bool:
    return importlib.util.find_spec("hm_pyo3") is not None


def _load_module() -> ModuleType:
    global _MODULE
    if _MODULE is not None:
        return _MODULE
    try:
        _MODULE = importlib.import_module("hm_pyo3")
    except ImportError as exc:
        raise RuntimeError(MISSING_RUST_MESSAGE) from exc
    return _MODULE


def transport_digest(
    local_steps: int,
    bridge_crossings: int,
    prompt_count: int,
    backend_name: str,
) -> tuple[int, int, float]:
    return _load_module().transport_digest(
        local_steps,
        bridge_crossings,
        prompt_count,
        backend_name,
    )


def signed_sketch_from_counts(
    positive_components: int,
    negative_components: int,
    cancellation_pairs: int,
    cycle_hint: int,
) -> tuple[int, int, int, int]:
    return _load_module().signed_sketch_from_counts(
        positive_components,
        negative_components,
        cancellation_pairs,
        cycle_hint,
    )


def sparse_batch_summary(ids: list[int], values: list[float]) -> tuple[int, bool]:
    return _load_module().sparse_batch_summary(ids, values)


def bridge_dependence(local_steps: int, bridge_crossings: int) -> float:
    return _load_module().bridge_dependence(local_steps, bridge_crossings)


def exact_persistence(
    family: str,
    backend_name: str,
    node_ids: list[int],
    edges: list[tuple[int, int]],
    vertex_filtration: list[float],
    edge_filtration: list[float],
    positive_components: int,
    negative_components: int,
    cancellation_pairs: int,
    cycle_hint: int,
    local_steps: int,
    bridge_crossings: int,
    retention_score: float,
) -> list[tuple[int, list[tuple[float, float | None]]]]:
    return _load_module().exact_persistence(
        family,
        backend_name,
        node_ids,
        edges,
        vertex_filtration,
        edge_filtration,
        positive_components,
        negative_components,
        cancellation_pairs,
        cycle_hint,
        local_steps,
        bridge_crossings,
        retention_score,
    )


def trace_schema_keys() -> list[str]:
    return _load_module().trace_schema_keys()
