from hybrid_mechlab import HybridLab, profiles


def test_trace_summary_and_schema():
    lab = HybridLab.attach(model="dummy", profile=profiles.reference.qwen35(), backend="adapter")
    trace = lab.run(prompts=["hi"], capture=("codes", "transport"))
    assert "trace" in trace.summary()
    assert trace.schema_keys()[0] == "trace_id"
    assert trace.to_record()["backend"] == "adapter"


def test_compare_native_vs_liger_uses_same_schema():
    native_trace = HybridLab.attach(
        model="dummy",
        profile=profiles.native.gated_deltanet(),
        backend="native",
    ).run(prompts=["compare transport"])
    liger_trace = HybridLab.attach(
        model="dummy",
        family="gated_deltanet",
        backend="liger",
    ).run(prompts=["compare transport"])
    report = native_trace.compare(liger_trace)
    assert report.schema_match is True
