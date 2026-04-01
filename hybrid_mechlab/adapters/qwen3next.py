"""Qwen3-Next adapter aliasing the Qwen3.5 reference path until a dedicated profile exists."""

from __future__ import annotations

from .qwen35 import Adapter as Qwen35Adapter


class Adapter(Qwen35Adapter):
    pass
