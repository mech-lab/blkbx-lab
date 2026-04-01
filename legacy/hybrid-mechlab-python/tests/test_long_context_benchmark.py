from hybrid_mechlab.experiments.long_context import run_long_context_benchmark
from hybrid_mechlab import profiles


def test_long_context_benchmark_reports_best_profile():
    report = run_long_context_benchmark(
        model="dummy",
        profiles=(profiles.reference.qwen35(), profiles.native.gated_deltanet()),
    )
    assert report.wedge == "long_context_reasoning"
    assert len(report.results) == 2
    assert report.best_retention_profile()
