"""Math backend selection and lazy Rust loading."""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

import hybrid_mechlab._rust as rust_shim
from hybrid_mechlab.kernel.schedule import ScheduleStats
from hybrid_mechlab.kernel.transport import TransportSummary, simulate_transport

if TYPE_CHECKING:
    from hybrid_mechlab.kernel.persistence import PersistenceDiagram, PersistenceInput
    from hybrid_mechlab.kernel.topology import SignedSketch


_MISSING_RUST_MESSAGE = (
    "math_backend='rust' requires the optional hybrid-mechlab-rust companion package"
)


class MathKernelBackend(Protocol):
    name: str

    def transport_summary(
        self,
        schedule_stats: ScheduleStats,
        *,
        prompt_count: int,
        backend_name: str,
    ) -> TransportSummary: ...

    def signed_sketch_from_counts(
        self,
        *,
        positive_components: int,
        negative_components: int,
        cancellation_pairs: int,
        cycle_hint: int,
    ) -> "SignedSketch": ...

    def sparse_batch_summary(self, ids: list[int], values: list[float]) -> tuple[int, bool]: ...

    def bridge_dependence(self, *, local_steps: int, bridge_crossings: int) -> float: ...

    def compute_exact_persistence(
        self,
        persistence_input: "PersistenceInput",
    ) -> tuple["PersistenceDiagram", ...]: ...


class _PythonMathKernelBackend:
    name = "python"

    def transport_summary(
        self,
        schedule_stats: ScheduleStats,
        *,
        prompt_count: int,
        backend_name: str,
    ) -> TransportSummary:
        return simulate_transport(
            schedule_stats,
            prompt_count=prompt_count,
            backend_name=backend_name,
        )

    def signed_sketch_from_counts(
        self,
        *,
        positive_components: int,
        negative_components: int,
        cancellation_pairs: int,
        cycle_hint: int,
    ):
        from hybrid_mechlab.kernel.topology import signed_sketch_from_counts

        return signed_sketch_from_counts(
            positive_components=positive_components,
            negative_components=negative_components,
            cancellation_pairs=cancellation_pairs,
            cycle_hint=cycle_hint,
        )

    def sparse_batch_summary(self, ids: list[int], values: list[float]) -> tuple[int, bool]:
        if len(ids) != len(values):
            raise ValueError("ids and values must have the same length")
        return len(ids), bool(ids)

    def bridge_dependence(self, *, local_steps: int, bridge_crossings: int) -> float:
        total = max(local_steps + bridge_crossings, 1)
        return bridge_crossings / total

    def compute_exact_persistence(self, persistence_input: "PersistenceInput"):
        from hybrid_mechlab.kernel.persistence import _compute_exact_persistence_python

        return _compute_exact_persistence_python(persistence_input)


class _RustMathKernelBackend:
    name = "rust"

    def __init__(self) -> None:
        if not rust_shim.available():
            raise RuntimeError(_MISSING_RUST_MESSAGE)

    def transport_summary(
        self,
        schedule_stats: ScheduleStats,
        *,
        prompt_count: int,
        backend_name: str,
    ) -> TransportSummary:
        local_steps, bridge_crossings, retention = rust_shim.transport_digest(
            schedule_stats.local_steps,
            schedule_stats.bridge_count,
            prompt_count,
            backend_name,
        )
        return TransportSummary(
            local_steps=local_steps,
            bridge_crossings=bridge_crossings,
            retention_score=retention,
            backend=backend_name,
        )

    def signed_sketch_from_counts(
        self,
        *,
        positive_components: int,
        negative_components: int,
        cancellation_pairs: int,
        cycle_hint: int,
    ):
        from hybrid_mechlab.kernel.topology import signed_sketch_from_counts

        values = rust_shim.signed_sketch_from_counts(
            positive_components,
            negative_components,
            cancellation_pairs,
            cycle_hint,
        )
        return signed_sketch_from_counts(
            positive_components=values[0],
            negative_components=values[1],
            cancellation_pairs=values[2],
            cycle_hint=values[3],
        )

    def sparse_batch_summary(self, ids: list[int], values: list[float]) -> tuple[int, bool]:
        return rust_shim.sparse_batch_summary(ids, values)

    def bridge_dependence(self, *, local_steps: int, bridge_crossings: int) -> float:
        return float(rust_shim.bridge_dependence(local_steps, bridge_crossings))

    def compute_exact_persistence(self, persistence_input: "PersistenceInput"):
        from hybrid_mechlab.kernel.persistence import BirthDeathPair, PersistenceDiagram

        raw_diagrams = rust_shim.exact_persistence(
            persistence_input.family,
            persistence_input.backend,
            [int(node) for node in persistence_input.graph.nodes.tolist()],
            list(persistence_input.graph.edge_tuples()),
            [float(value) for value in persistence_input.vertex_filtration.tolist()],
            [float(value) for value in persistence_input.edge_filtration.tolist()],
            persistence_input.signed_sketch.positive_components,
            persistence_input.signed_sketch.negative_components,
            persistence_input.signed_sketch.cancellation_pairs,
            persistence_input.signed_sketch.cycle_hint,
            persistence_input.local_steps,
            persistence_input.bridge_crossings,
            persistence_input.retention_score,
        )
        diagrams = []
        for dimension, pairs in raw_diagrams:
            diagrams.append(
                PersistenceDiagram(
                    dimension=int(dimension),
                    pairs=tuple(
                        BirthDeathPair(
                            dimension=int(dimension),
                            birth=round(float(birth), 6),
                            death=None if death is None else round(float(death), 6),
                        )
                        for birth, death in pairs
                    ),
                )
            )
        return tuple(diagrams)


_PYTHON_BACKEND: MathKernelBackend = _PythonMathKernelBackend()


def get_math_backend(name: str | None = None) -> MathKernelBackend:
    selected = (name or "python").lower()
    if selected == "python":
        return _PYTHON_BACKEND
    if selected == "rust":
        return _RustMathKernelBackend()
    raise ValueError(f"unknown math backend: {name}")
