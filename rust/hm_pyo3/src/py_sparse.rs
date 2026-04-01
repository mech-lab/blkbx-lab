use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

#[pyfunction]
pub fn sparse_batch_summary(ids: Vec<u32>, values: Vec<f32>) -> PyResult<(usize, bool)> {
    if ids.len() != values.len() {
        return Err(PyValueError::new_err("ids and values must have the same length"));
    }
    Ok((ids.len(), !ids.is_empty()))
}
