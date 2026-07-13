from __future__ import annotations

from hybrid_mechlab import HybridLab, profiles
from hybrid_mechlab.kernel.geometry import HolonomRisk
from hybrid_mechlab.topology import geometry


def _qwen_trace():
    return HybridLab.attach(
        model="dummy-qwen",
        profile=profiles.reference.qwen35(),
        backend="adapter",
    ).run(prompts=["Measure experimental holonom risk."])


def test_trace_geodesic_exposes_a_discrete_path():
    trace = _qwen_trace()
    geodesic = geometry.trace_geodesic(trace)

    assert geodesic.node_ids[0] == 0
    assert geodesic.node_ids[-1] == len(trace.schedule.ops)
    assert len(geodesic.segments) == len(geodesic.node_ids) - 1
    assert geodesic.total_cost > 0.0
    assert geodesic.shortcut_gain >= 0.0
    assert geodesic.curvature_proxy >= 0.0


def test_trace_holonom_returns_named_risk_unit():
    trace = _qwen_trace()
    holonom = trace.holonom()

    assert isinstance(holonom, HolonomRisk)
    assert holonom.holonom.unit == "holonom"
    assert holonom.holonom.value > 0.0
    assert holonom.bridge_dependence == trace.bridge_dependence()
    assert holonom.tract_retention == trace.tract_retention()


def test_holonom_risk_differs_across_transport_families():
    qwen_trace = _qwen_trace()
    gated_trace = HybridLab.attach(
        model="dummy-native",
        profile=profiles.native.gated_deltanet(),
        backend="native",
    ).run(prompts=["Measure experimental holonom risk."])

    qwen_risk = qwen_trace.holonom()
    gated_risk = gated_trace.holonom()

    assert qwen_trace.profile.family.kind.value != gated_trace.profile.family.kind.value
    assert qwen_risk.holonom.value != gated_risk.holonom.value
