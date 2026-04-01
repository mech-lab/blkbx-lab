import json
from pathlib import Path

from hybrid_mechlab import HybridLab, profiles
from hybrid_mechlab.topology.offline import compute_persistence


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "rust_kernel_fixture.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_float_list_close(left, right, tol=1e-6):
    assert len(left) == len(right)
    for left_value, right_value in zip(left, right):
        assert abs(float(left_value) - float(right_value)) <= tol


def _assert_diagrams_match(report, fixture_record):
    assert len(report.diagrams) == len(fixture_record["diagrams"])
    for diagram, fixture_diagram in zip(report.diagrams, fixture_record["diagrams"]):
        assert diagram.dimension == fixture_diagram["dimension"]
        assert len(diagram.pairs) == len(fixture_diagram["pairs"])
        for pair, fixture_pair in zip(diagram.pairs, fixture_diagram["pairs"]):
            assert abs(pair.birth - fixture_pair["birth"]) <= 1e-6
            if fixture_pair["death"] is None:
                assert pair.death is None
            else:
                assert pair.death is not None
                assert abs(pair.death - fixture_pair["death"]) <= 1e-6


def _assert_report_matches_fixture(report, transport_digest, fixture_record):
    persistence_input = report.persistence_input.to_record()
    fixture_input = fixture_record["persistence_input"]

    assert len(report.persistence_input.graph.edges) == fixture_record["schedule"]["conformance"]["bridge_count"] + 4
    assert persistence_input["node_ids"] == fixture_input["node_ids"]
    assert persistence_input["edge_list"] == fixture_input["edge_list"]
    _assert_float_list_close(persistence_input["vertex_filtration"], fixture_input["vertex_filtration"])
    _assert_float_list_close(persistence_input["edge_filtration"], fixture_input["edge_filtration"])

    assert abs(report.summary.max_finite_persistence - fixture_record["summary"]["max_finite_persistence"]) <= 1e-6
    assert abs(report.summary.total_finite_persistence - fixture_record["summary"]["total_finite_persistence"]) <= 1e-6
    assert report.summary.h0_pairs == fixture_record["summary"]["h0_pairs"]
    assert report.summary.h1_pairs == fixture_record["summary"]["h1_pairs"]
    assert report.summary.infinite_pairs == fixture_record["summary"]["infinite_pairs"]
    assert transport_digest.local_steps == fixture_record["transport_digest"]["local_steps"]
    assert transport_digest.bridge_crossings == fixture_record["transport_digest"]["bridge_crossings"]
    assert abs(transport_digest.retention_score - fixture_record["transport_digest"]["retention_score"]) <= 1e-6
    _assert_diagrams_match(report, fixture_record)


def test_python_kernel_matches_rust_fixture_for_qwen35():
    trace = HybridLab.attach(
        model="dummy-qwen",
        profile=profiles.reference.qwen35(),
        backend="adapter",
    ).run(prompts=["Measure topology for a reference hybrid."])
    report = compute_persistence(trace)
    _assert_report_matches_fixture(report, trace.transport_digest, FIXTURE["profiles"]["qwen35"])


def test_python_kernel_matches_rust_fixture_for_gated_deltanet():
    trace = HybridLab.attach(
        model="dummy-native",
        profile=profiles.native.gated_deltanet(),
        backend="native",
    ).run(prompts=["Measure topology for a native kernel."])
    report = compute_persistence(trace)
    _assert_report_matches_fixture(report, trace.transport_digest, FIXTURE["profiles"]["gated_deltanet"])
