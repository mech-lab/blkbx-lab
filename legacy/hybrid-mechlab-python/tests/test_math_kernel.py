import pytest

from hybrid_mechlab import HybridLab, kernel, profiles
from hybrid_mechlab.topology.offline import compute_persistence


def test_sparse_vector_and_batch_summary():
    vector = kernel.SparseVector(ids=[1, 2], values=[0.1, 0.2])
    batch = kernel.SparseBatch(vectors=(vector,))

    assert vector.nnz == 2
    assert batch.nnz == 2
    assert batch.to_trace_records(("hook.test",))[0]["feature_ids"] == [1, 2]
    assert kernel.get_math_backend("python").sparse_batch_summary([1, 2], [0.1, 0.2]) == (2, True)


def test_hybridlab_defaults_to_python_math_backend_and_preserves_schema():
    trace = HybridLab.attach(
        model="dummy",
        profile=profiles.reference.qwen35(),
        backend="adapter",
    ).run(prompts=["hi"])

    assert trace.math_backend == "python"
    record = trace.to_record()
    assert "math_backend" not in record
    assert record["backend"] == "adapter"


def test_unknown_math_backend_raises():
    with pytest.raises(ValueError):
        kernel.get_math_backend("bogus")


def test_rust_math_backend_is_not_available():
    with pytest.raises(RuntimeError) as excinfo:
        HybridLab.attach(
            model="dummy",
            profile=profiles.reference.qwen35(),
            backend="adapter",
            math_backend="rust",
        )
    assert "python-only" in str(excinfo.value)

def test_compute_persistence_uses_python_backend():
    trace = HybridLab.attach(
        model="dummy",
        profile=profiles.reference.qwen35(),
        backend="adapter",
        math_backend="python",
    ).run(prompts=["measure kernel persistence"])
    report = compute_persistence(trace)
    assert report.summary.h0_pairs >= 1
