from hybrid_mechlab import HybridLab, profiles
from hybrid_mechlab.blt.sparse_codes import SparseCodeBatch


def test_sparse_code_batch_basic():
    batch = SparseCodeBatch(ids=[1, 2], values=[0.1, 0.2])
    assert len(batch.ids) == len(batch.values)


def test_trace_emits_family_agnostic_sparse_codes():
    trace = HybridLab.attach(
        model="dummy",
        profile=profiles.native.gated_deltanet(),
        backend="native",
    ).run(prompts=["emit codes"])
    assert trace.sparse_codes
    assert "feature_ids" in trace.sparse_codes[0]
