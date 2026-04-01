use pyo3::prelude::*;

#[pyfunction]
pub fn trace_schema_keys() -> Vec<&'static str> {
    vec![
        "trace_id",
        "prompt_count",
        "profile_name",
        "family",
        "backend",
        "schedule",
        "capture",
        "transport_digest",
        "signed_sketch",
        "reproducibility_manifest",
        "sparse_codes",
    ]
}
