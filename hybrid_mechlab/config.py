"""Typed experiment configs (placeholder)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ExperimentConfig:
    name: str
    prompts: List[str]
    capture: List[str]
    interventions: List[Dict[str, Any]] | None = None
