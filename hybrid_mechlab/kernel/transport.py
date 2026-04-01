"""Transport state helpers for the NumPy math kernel."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from hybrid_mechlab.kernel.schedule import ScheduleStats


@dataclass(frozen=True)
class TransportState:
    values: np.ndarray
    step_index: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "values",
            np.asarray(self.values, dtype=np.float32).reshape(-1),
        )


@dataclass(frozen=True)
class TransportSummary:
    local_steps: int
    bridge_crossings: int
    retention_score: float
    backend: str


def backend_factor(name: str) -> float:
    return {
        "adapter": 0.86,
        "native": 1.0,
        "liger": 0.94,
    }.get(name, 1.0)


def simulate_transport(
    schedule_stats: ScheduleStats,
    *,
    prompt_count: int,
    backend_name: str,
) -> TransportSummary:
    multiplier = max(prompt_count, 1)
    local_steps = schedule_stats.local_steps * multiplier
    bridge_crossings = schedule_stats.bridge_count * multiplier
    retention = ((local_steps + 1) / (local_steps + bridge_crossings + 1)) * backend_factor(
        backend_name
    )
    retention = round(float(retention), 4)
    return TransportSummary(
        local_steps=local_steps,
        bridge_crossings=bridge_crossings,
        retention_score=retention,
        backend=backend_name,
    )
