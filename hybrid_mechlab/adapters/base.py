"""Adapter contracts for understanding-first profiles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from hybrid_mechlab.profiles import ResearchProfile
from hybrid_mechlab.schedules import HybridSchedule


@dataclass(frozen=True)
class AdapterDescriptor:
    name: str
    hook_points: tuple[str, ...]


class HybridAdapter(Protocol):
    descriptor: AdapterDescriptor

    def profile(self) -> ResearchProfile: ...
    def schedule(self) -> HybridSchedule: ...
    def hook_points(self) -> tuple[str, ...]: ...
    def attach_hooks(self, model: Any, capture_policy: Any) -> Any: ...
    def extract_state(self, raw_hook_output: Any, hook_id: str) -> Any: ...
    def bridge_mask(self) -> list[bool]: ...


class BaseAdapter:
    descriptor = AdapterDescriptor(name="base", hook_points=())

    def __init__(self, profile: ResearchProfile) -> None:
        self._profile = profile

    def profile(self) -> ResearchProfile:
        return self._profile

    def schedule(self) -> HybridSchedule:
        return self._profile.schedule

    def hook_points(self) -> tuple[str, ...]:
        return self.descriptor.hook_points or self._profile.hook_points

    def attach_hooks(self, model: Any, capture_policy: Any) -> dict[str, Any]:
        return {
            "model": model,
            "capture_policy": capture_policy,
            "hook_points": self.hook_points(),
        }

    def extract_state(self, raw_hook_output: Any, hook_id: str) -> Any:
        return {"hook_id": hook_id, "state": raw_hook_output}

    def bridge_mask(self) -> list[bool]:
        return self._profile.schedule.bridge_mask()
