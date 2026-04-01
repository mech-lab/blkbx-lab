from hybrid_mechlab import HybridLab, profiles
from hybrid_mechlab.topology import sheaf


def test_partial_sheaf_empty():
    view = sheaf.build_partial_sheaf(trace=None)
    assert view.gluing_report().sections == tuple()


def test_partial_sheaf_builds_sections_from_trace():
    trace = HybridLab.attach(
        model="dummy",
        profile=profiles.reference.qwen35(),
        backend="adapter",
    ).run(prompts=["map the sections"])
    view = sheaf.build_partial_sheaf(trace=trace)
    report = view.gluing_report()
    assert len(report.sections) == len(trace.sparse_codes)
