"""Deterministic scalar metrics for traces and topology reports."""

from __future__ import annotations


def bridge_dependence(local_steps: int, bridge_crossings: int) -> float:
    total = max(local_steps + bridge_crossings, 1)
    return bridge_crossings / total


def tract_retention(retention_score: float) -> float:
    return retention_score


def topological_susceptibility(
    positive_components: int,
    negative_components: int,
    cancellation_pairs: int,
) -> float:
    total = max(positive_components + negative_components, 1)
    return cancellation_pairs / total
