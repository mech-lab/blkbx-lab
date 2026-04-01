use pyo3::prelude::*;

mod py_metrics;
mod py_schedule;
mod py_sparse;
mod py_topology;
mod py_trace;

#[pymodule]
fn hm_pyo3(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(py_schedule::native_family_names, m)?)?;
    m.add_function(wrap_pyfunction!(py_schedule::describe_schedule, m)?)?;
    m.add_function(wrap_pyfunction!(py_schedule::kernel_conformance, m)?)?;
    m.add_function(wrap_pyfunction!(py_trace::trace_schema_keys, m)?)?;
    m.add_function(wrap_pyfunction!(py_sparse::sparse_batch_summary, m)?)?;
    m.add_function(wrap_pyfunction!(py_topology::signed_sketch_from_counts, m)?)?;
    m.add_function(wrap_pyfunction!(py_topology::exact_persistence, m)?)?;
    m.add_function(wrap_pyfunction!(py_metrics::bridge_dependence, m)?)?;
    m.add_function(wrap_pyfunction!(py_metrics::transport_digest, m)?)?;
    Ok(())
}
