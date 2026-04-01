"""Qwen3.5 reference adapter."""

from __future__ import annotations

from hybrid_mechlab.profiles import reference

from .base import AdapterDescriptor, BaseAdapter


class Adapter(BaseAdapter):
    descriptor = AdapterDescriptor(
        name="qwen35",
        hook_points=("block.recurrent", "block.bridge"),
    )

    def __init__(self) -> None:
        super().__init__(reference.qwen35())
