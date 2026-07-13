"""Experimental geometry helpers that derive holonom risk from trace geodesics."""

from __future__ import annotations

from hybrid_mechlab.api import TraceHandle, backend_name
from hybrid_mechlab.kernel.geometry import GeodesicPath, HolonomRisk, actuarial_holonom, discrete_geodesic
from hybrid_mechlab.topology.offline import trace_graph_inputs
from hybrid_mechlab.topology.sheaf import build_partial_sheaf


def trace_geodesic(trace: TraceHandle, *, bridge_penalty: float = 0.35) -> GeodesicPath:
    graph, path_edges, bridge_edges = trace_graph_inputs(trace)
    return discrete_geodesic(
        graph,
        path_edges=path_edges,
        bridge_edges=bridge_edges,
        bridge_penalty=bridge_penalty,
    )


def holonom_risk(trace: TraceHandle, *, bridge_penalty: float = 0.35) -> HolonomRisk:
    geodesic = trace_geodesic(trace, bridge_penalty=bridge_penalty)
    gluing_report = build_partial_sheaf(trace, basis="block_supernodes").gluing_report()
    return actuarial_holonom(
        geodesic,
        bridge_dependence=trace.bridge_dependence(),
        tract_retention=trace.tract_retention(),
        gluing_defect=gluing_report.defect_score,
        family=trace.profile.family.kind.value,
        backend=backend_name(trace.backend),
    )
