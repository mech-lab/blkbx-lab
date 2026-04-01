use pyo3::prelude::*;

#[pyfunction]
pub fn bridge_dependence(local_steps: usize, bridge_crossings: usize) -> f32 {
    let total = (local_steps + bridge_crossings).max(1);
    bridge_crossings as f32 / total as f32
}

#[pyfunction]
pub fn transport_digest(
    local_steps: usize,
    bridge_crossings: usize,
    prompt_count: usize,
    backend_name: &str,
) -> (usize, usize, f32) {
    let multiplier = prompt_count.max(1);
    let total_local_steps = local_steps * multiplier;
    let total_bridge_crossings = bridge_crossings * multiplier;
    let backend_factor = match backend_name {
        "adapter" => 0.86,
        "native" => 1.0,
        "liger" => 0.94,
        _ => 1.0,
    };
    let retention = ((total_local_steps + 1) as f32
        / (total_local_steps + total_bridge_crossings + 1) as f32)
        * backend_factor;
    (
        total_local_steps,
        total_bridge_crossings,
        (retention * 10_000.0).round() / 10_000.0,
    )
}
