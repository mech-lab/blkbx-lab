use std::path::PathBuf;

use inkreceipts_host::HostError;
use pyo3::create_exception;
use pyo3::exceptions::{PyException, PyOSError};
use pyo3::prelude::*;

create_exception!(blkbx_lab, InkError, PyException);
create_exception!(blkbx_lab, InkSchemaError, InkError);
create_exception!(blkbx_lab, InkUnsafePathError, InkError);
create_exception!(blkbx_lab, InkTrustError, InkError);
create_exception!(blkbx_lab, InkVerificationError, InkError);
create_exception!(blkbx_lab, InkEvidenceValidationError, InkError);

fn to_json_string(value: serde_json::Value) -> PyResult<String> {
    serde_json::to_string(&value)
        .map_err(|err| InkSchemaError::new_err(format!("failed to serialize JSON: {err}")))
}

fn map_host_error(err: HostError) -> PyErr {
    match err {
        HostError::Io(err) => PyOSError::new_err(err.to_string()),
        HostError::Json(err) => InkSchemaError::new_err(err.to_string()),
        HostError::Core(err) => InkVerificationError::new_err(format!("{err:?}")),
        HostError::InvalidInput(message) => InkEvidenceValidationError::new_err(message),
        HostError::UnsafePath(message) => InkUnsafePathError::new_err(message),
        HostError::Trust(message) => InkTrustError::new_err(message),
    }
}

#[pyfunction]
#[pyo3(signature = (bundle_dir, action_id, artifacts_json, created_at=None))]
fn create_manifest(
    bundle_dir: PathBuf,
    action_id: String,
    artifacts_json: String,
    created_at: Option<String>,
) -> PyResult<String> {
    inkreceipts_host::create_manifest(
        &bundle_dir,
        &action_id,
        &artifacts_json,
        created_at.as_deref(),
    )
    .map_err(map_host_error)
    .and_then(to_json_string)
}

#[pyfunction]
#[pyo3(signature = (manifest_path, policy_path, controls_json=None))]
fn analyze(
    manifest_path: PathBuf,
    policy_path: PathBuf,
    controls_json: Option<String>,
) -> PyResult<String> {
    inkreceipts_host::analyze(&manifest_path, &policy_path, controls_json.as_deref())
        .map_err(map_host_error)
        .and_then(to_json_string)
}

#[pyfunction]
#[pyo3(signature = (manifest_path, policy_path, controls_json=None, output_path=None, demo_signer=false))]
fn gate(
    manifest_path: PathBuf,
    policy_path: PathBuf,
    controls_json: Option<String>,
    output_path: Option<PathBuf>,
    demo_signer: bool,
) -> PyResult<String> {
    inkreceipts_host::gate(
        &manifest_path,
        &policy_path,
        controls_json.as_deref(),
        output_path.as_deref(),
        demo_signer,
    )
    .map_err(map_host_error)
    .and_then(to_json_string)
}

#[pyfunction]
#[pyo3(signature = (receipt_path, manifest_path=None))]
fn verify(receipt_path: PathBuf, manifest_path: Option<PathBuf>) -> PyResult<String> {
    inkreceipts_host::verify(&receipt_path, manifest_path.as_deref())
        .map_err(map_host_error)
        .and_then(to_json_string)
}

#[pyfunction]
#[pyo3(signature = (left_receipt, right_receipt, output_path=None))]
fn compare(
    left_receipt: PathBuf,
    right_receipt: PathBuf,
    output_path: Option<PathBuf>,
) -> PyResult<String> {
    inkreceipts_host::compare(&left_receipt, &right_receipt, output_path.as_deref())
        .map_err(map_host_error)
        .and_then(to_json_string)
}

#[pyfunction]
#[pyo3(signature = (initialize_local_issuer=false))]
fn doctor(initialize_local_issuer: bool) -> PyResult<String> {
    inkreceipts_host::doctor(initialize_local_issuer)
        .map_err(map_host_error)
        .and_then(to_json_string)
}

#[pymodule]
fn _ink_native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("InkError", m.py().get_type::<InkError>())?;
    m.add("InkSchemaError", m.py().get_type::<InkSchemaError>())?;
    m.add(
        "InkUnsafePathError",
        m.py().get_type::<InkUnsafePathError>(),
    )?;
    m.add("InkTrustError", m.py().get_type::<InkTrustError>())?;
    m.add(
        "InkVerificationError",
        m.py().get_type::<InkVerificationError>(),
    )?;
    m.add(
        "InkEvidenceValidationError",
        m.py().get_type::<InkEvidenceValidationError>(),
    )?;
    m.add_function(wrap_pyfunction!(create_manifest, m)?)?;
    m.add_function(wrap_pyfunction!(analyze, m)?)?;
    m.add_function(wrap_pyfunction!(gate, m)?)?;
    m.add_function(wrap_pyfunction!(verify, m)?)?;
    m.add_function(wrap_pyfunction!(compare, m)?)?;
    m.add_function(wrap_pyfunction!(doctor, m)?)?;
    Ok(())
}
