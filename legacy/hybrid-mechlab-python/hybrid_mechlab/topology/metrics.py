"""Topology and transport metrics."""

from __future__ import annotations

from hybrid_mechlab.api import TraceHandle
from hybrid_mechlab.kernel import metrics as kernel_metrics


def bridge_dependence(trace: TraceHandle) -> float:
    return kernel_metrics.bridge_dependence(
        trace.transport_digest.local_steps,
        trace.transport_digest.bridge_crossings,
    )


def tract_retention(trace: TraceHandle) -> float:
    return kernel_metrics.tract_retention(trace.transport_digest.retention_score)


def topological_susceptibility(trace: TraceHandle) -> float:
    return kernel_metrics.topological_susceptibility(
        trace.signed_sketch.positive_components,
        trace.signed_sketch.negative_components,
        trace.signed_sketch.cancellation_pairs,
    )
