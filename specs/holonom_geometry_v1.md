# Holonom Geometry v1

- This is an experimental research-only extension in `hybrid_mechlab`, not part of the canonical `blkbx-lab` release contract.
- The `holonom` is a provisional actuarial-style risk unit derived from a discrete geodesic over the trace transport graph.
- Geodesics are computed across the existing trace graph with edge classes:
  - `path`
  - `bridge`
  - `closure`
- The experimental risk bundle combines:
  - total geodesic cost
  - bridge participation
  - shortcut gain across long-range transport
  - sheaf gluing defect
  - tract retention stabilization
- Public research entry points:
  - `TraceHandle.geodesic()`
  - `TraceHandle.holonom()`
  - `hybrid_mechlab.topology.geometry.trace_geodesic()`
  - `hybrid_mechlab.topology.geometry.holonom_risk()`
