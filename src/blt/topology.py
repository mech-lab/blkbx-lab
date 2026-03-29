from __future__ import annotations

from collections import Counter
from typing import Any


def build_topology_summary(trace: dict[str, Any], blt_code_rows: list[dict[str, Any]]) -> dict[str, Any]:
    group_counts = Counter(row["code_group"] for row in blt_code_rows)
    component_count = max(1, len(group_counts))
    mean_degree = round(sum(group_counts.values()) / component_count, 6)
    bridge_discontinuity = round(sum(row["bridge_strength"] for row in blt_code_rows) / max(len(blt_code_rows), 1), 6)
    susceptibility = round(sum(row["reconstruction_error"] for row in blt_code_rows) / max(len(blt_code_rows), 1), 6)
    return {
        "trace_id": trace["trace_id"],
        "topology_backend": "sketch",
        "scope": "trace",
        "bridge_policy": "bridge-aware",
        "intervention_axis": "code_group",
        "summary_metrics": {
            "component_count": component_count,
            "mean_degree": mean_degree,
            "bridge_discontinuity": bridge_discontinuity,
            "topological_susceptibility": susceptibility,
            "token_count": len(trace["tokens"]),
            "block_count": trace["block_count"],
        },
    }
