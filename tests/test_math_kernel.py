import importlib.util

import pytest

from hybrid_mechlab import HybridLab, kernel, profiles
import hybrid_mechlab._rust as rust_shim
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


def test_rust_math_backend_missing_extension_raises_clear_error(monkeypatch):
    monkeypatch.setattr(rust_shim, "available", lambda: False)
    with pytest.raises(RuntimeError) as excinfo:
        HybridLab.attach(
            model="dummy",
            profile=profiles.reference.qwen35(),
            backend="adapter",
            math_backend="rust",
        )
    assert str(excinfo.value) == rust_shim.MISSING_RUST_MESSAGE


def test_rust_math_backend_matches_python_when_extension_is_available():
    if importlib.util.find_spec("hm_pyo3") is None:
        pytest.skip("hm_pyo3 extension is not installed")

    python_trace = HybridLab.attach(
        model="dummy",
        profile=profiles.reference.qwen35(),
        backend="adapter",
        math_backend="python",
    ).run(prompts=["measure kernel parity"])
    rust_trace = HybridLab.attach(
        model="dummy",
        profile=profiles.reference.qwen35(),
        backend="adapter",
        math_backend="rust",
    ).run(prompts=["measure kernel parity"])

    assert python_trace.transport_digest == rust_trace.transport_digest
    assert python_trace.signed_sketch == rust_trace.signed_sketch

    python_report = compute_persistence(python_trace)
    rust_report = compute_persistence(rust_trace)
    assert python_report.persistence_input.to_record() == rust_report.persistence_input.to_record()
    assert python_report.summary == rust_report.summary
