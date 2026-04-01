"""OLMo Hybrid reference adapter."""

from __future__ import annotations

from hybrid_mechlab.profiles import reference

from .base import AdapterDescriptor, BaseAdapter


class Adapter(BaseAdapter):
    descriptor = AdapterDescriptor(
        name="olmo_hybrid",
        hook_points=("block.local", "block.bridge"),
    )

    def __init__(self) -> None:
        super().__init__(reference.olmo_hybrid())
