"""Math backend selection for the Python-only split."""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

from hybrid_mechlab.kernel.schedule import ScheduleStats
from hybrid_mechlab.kernel.transport import TransportSummary, simulate_transport

if TYPE_CHECKING:
    from hybrid_mechlab.kernel.persistence import PersistenceDiagram, PersistenceInput
    from hybrid_mechlab.kernel.topology import SignedSketch


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


_PYTHON_BACKEND: MathKernelBackend = _PythonMathKernelBackend()


def get_math_backend(name: str | None = None) -> MathKernelBackend:
    selected = (name or "python").lower()
    if selected == "python":
        return _PYTHON_BACKEND
    if selected == "rust":
        raise RuntimeError("this repo is python-only; math_backend='rust' is not available")
    raise ValueError(f"unknown math backend: {name}")
