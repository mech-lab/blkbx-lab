"""Online topology sketch helpers."""

from __future__ import annotations

from hybrid_mechlab.api import SignedSketchRecord, TraceHandle
from hybrid_mechlab.kernel.topology import signed_sketch_from_counts


def signed_sketch(trace: TraceHandle) -> SignedSketchRecord:
    sketch = signed_sketch_from_counts(
        positive_components=trace.signed_sketch.positive_components,
        negative_components=trace.signed_sketch.negative_components,
        cancellation_pairs=trace.signed_sketch.cancellation_pairs,
        cycle_hint=trace.signed_sketch.cycle_hint,
    )
    return SignedSketchRecord(**sketch.to_record())
