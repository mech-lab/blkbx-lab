"""Custom adapter for user-supplied schedules."""

from __future__ import annotations

from hybrid_mechlab.profiles import BackendKind, ResearchProfile
from hybrid_mechlab.schedules import HybridSchedule

from .base import AdapterDescriptor, BaseAdapter


class Adapter(BaseAdapter):
    descriptor = AdapterDescriptor(name="custom", hook_points=("custom.local", "custom.bridge"))

    def __init__(self, schedule: HybridSchedule) -> None:
        profile = ResearchProfile(
            name="reference.custom",
            family=schedule.family,
            schedule=schedule,
            backend=BackendKind.adapter,
            hook_points=self.descriptor.hook_points,
            source_adapter="hybrid_mechlab.adapters.custom",
        )
        super().__init__(profile)
