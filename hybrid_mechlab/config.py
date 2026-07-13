"""Experimental typed configs kept for research, not the public BLKBX surface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ExperimentConfig:
    name: str
    prompts: list[str]
    capture: list[str]
    interventions: list[dict[str, Any]] | None = None
