"""Kimi Linear reference adapter."""

from __future__ import annotations

from hybrid_mechlab.profiles import reference

from .base import AdapterDescriptor, BaseAdapter


class Adapter(BaseAdapter):
    descriptor = AdapterDescriptor(
        name="kimi_linear",
        hook_points=("block.linear", "block.bridge"),
    )

    def __init__(self) -> None:
        super().__init__(reference.kimi_linear())
