from hybrid_mechlab import HybridLab, profiles
from hybrid_mechlab.topology import metrics


def test_bridge_dependence_for_reference_trace():
    trace = HybridLab.attach(
        model="dummy",
        profile=profiles.reference.qwen35(),
        backend="adapter",
    ).run(prompts=["measure bridge dependence"])
    assert metrics.bridge_dependence(trace) > 0.0
    assert metrics.tract_retention(trace) > 0.0
