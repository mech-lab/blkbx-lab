use hm_core::family::TransportFamilyKind;
use hm_core::native::{
    gated_deltanet_kernel, hawk_kernel, hgrn2_kernel, retnet_kernel, transnormer_llm_kernel,
    validate_kernel, NativeTransportKernel,
};
use hm_core::schedule::HybridSchedule;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

fn kernel_for_name(name: &str) -> PyResult<hm_core::native::CanonicalTransportKernel> {
    match name {
        "gated_deltanet" => Ok(gated_deltanet_kernel()),
        "hgrn2" => Ok(hgrn2_kernel()),
        "retnet" => Ok(retnet_kernel()),
        "hawk" => Ok(hawk_kernel()),
        "transnormer_llm" => Ok(transnormer_llm_kernel()),
        _ => Err(PyValueError::new_err(format!("unknown native family: {name}"))),
    }
}

fn schedule_to_rows(schedule: &HybridSchedule) -> Vec<(String, u16)> {
    schedule
        .ops
        .iter()
        .map(|op| (format!("{:?}", op.kind), op.local_index))
        .collect()
}

#[pyfunction]
pub fn native_family_names() -> Vec<&'static str> {
    vec![
        "gated_deltanet",
        "hgrn2",
        "retnet",
        "hawk",
        "transnormer_llm",
    ]
}

#[pyfunction]
pub fn describe_schedule(family: &str) -> PyResult<Vec<(String, u16)>> {
    let kernel = kernel_for_name(family)?;
    Ok(schedule_to_rows(kernel.schedule()))
}

#[pyfunction]
pub fn kernel_conformance(family: &str) -> PyResult<(String, bool, usize, usize)> {
    let kernel = kernel_for_name(family)?;
    let report = validate_kernel(&kernel);
    let family_name = match report.family {
        TransportFamilyKind::GatedDeltaNet => "gated_deltanet",
        TransportFamilyKind::HGRN2 => "hgrn2",
        TransportFamilyKind::RetNet => "retnet",
        TransportFamilyKind::Hawk => "hawk",
        TransportFamilyKind::TransNormerLLM => "transnormer_llm",
        _ => "other",
    };
    Ok((
        family_name.to_string(),
        report.passed,
        report.schedule_length,
        report.bridge_count,
    ))
}
