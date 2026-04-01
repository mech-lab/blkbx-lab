"""Partial sheaf utilities."""

from __future__ import annotations

from hybrid_mechlab.api import TraceHandle
from hybrid_mechlab.kernel.sheaf import (
    GluingReport,
    PartialSection,
    PartialSheaf,
    build_partial_sheaf as build_kernel_partial_sheaf,
)


class PartialSheafView(PartialSheaf):
    pass


def build_partial_sheaf(trace: TraceHandle | None, basis: str = "block_supernodes") -> PartialSheafView:
    if trace is None:
        return PartialSheafView(sections=tuple(), defect_score=0.0)
    built = build_kernel_partial_sheaf(
        trace.sparse_codes,
        basis=basis,
        cancellation_pairs=trace.signed_sketch.cancellation_pairs,
    )
    return PartialSheafView(sections=built.sections, defect_score=built.defect_score)
