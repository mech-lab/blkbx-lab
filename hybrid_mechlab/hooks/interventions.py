"""Experimental intervention primitives outside the BLKBX release surface."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FeatureClamp:
    target: str
    feature_id: int
    value: float


@dataclass
class BridgeGateScale:
    target: str
    scale: float
