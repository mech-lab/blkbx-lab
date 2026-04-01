"""Schedule analysis utilities backed by NumPy arrays."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from hybrid_mechlab.schedules import HybridSchedule, TransportRegimeKind


@dataclass(frozen=True)
class ScheduleStats:
    length: int
    local_steps: int
    bridge_count: int
    bridge_mask: np.ndarray


def analyze_schedule(schedule: HybridSchedule) -> ScheduleStats:
    bridge_mask = np.asarray(
        [op.kind == TransportRegimeKind.global_bridge for op in schedule.ops],
        dtype=np.bool_,
    )
    bridge_count = int(np.count_nonzero(bridge_mask))
    return ScheduleStats(
        length=len(schedule.ops),
        local_steps=len(schedule.ops) - bridge_count,
        bridge_count=bridge_count,
        bridge_mask=bridge_mask,
    )
