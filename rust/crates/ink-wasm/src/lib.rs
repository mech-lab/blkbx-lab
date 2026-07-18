#![forbid(unsafe_code)]

use ink_core::bounded::{IssuerId, PublicKeyId};
use ink_core::canon;
use ink_receipt_v2::{VerificationCheck, VerificationReportJson};
use ink_verify::TrustedIssuerKey;
use ink_verify::{ReceiptVerificationReport, VerificationPolicy};
use serde::Deserialize;
use serde_json::Value;
#[cfg(target_arch = "wasm32")]
use wasm_bindgen::prelude::*;

fn receipt_report_json(report: &ReceiptVerificationReport) -> String {
    format!(
        "{{\"structural_valid\":{},\"status\":\"{}\",\"code\":\"{}\"}}",
        report.core.valid,
        report.status.as_str(),
        report.code.as_str()
    )
}

fn error_json(code: &str) -> String {
    format!(
        "{{\"structural_valid\":false,\"status\":\"error\",\"code\":\"{}\"}}",
        code
    )
}

#[derive(Debug, Deserialize)]
struct ArtifactInput {
    receipt: Option<Value>,
    manifest: Option<Value>,
    verification_policy: Option<Value>,
    trust_registry: Option<Value>,
    revocations: Option<Value>,
}

fn invalid_artifact_report(code: &str, message: &str) -> VerificationReportJson {
    VerificationReportJson {
        schema: "ink.verification-report.v1".to_string(),
        status: "invalid".to_string(),
        code: code.to_string(),
        summary_status: "fail".to_string(),
        summary_text: message.to_string(),
        transcript_encoding: "unknown".to_string(),
        receipt_profile: "unknown".to_string(),
        issuer: "unknown".to_string(),
        key_id: "unknown".to_string(),
        payload_digest_alg: "unknown".to_string(),
        payload_digest_hex: "unavailable".to_string(),
        signature_valid: false,
        trusted_issuer: false,
        revocation_checked: false,
        revocation_ok: false,
        policy_accepted: false,
        verification_engine: "Rust ink-wasm".to_string(),
        network_required: false,
        scope: "receipt-only".to_string(),
        checks: vec![VerificationCheck {
            id: "artifacts.input".to_string(),
            status: "fail".to_string(),
            reason_code: code.to_string(),
        }],
    }
}

fn render_artifact_report(report: &VerificationReportJson) -> String {
    serde_json::to_string_pretty(report).unwrap_or_else(|err| {
        format!(
            "{{\"schema\":\"ink.verification-report.v1\",\"status\":\"invalid\",\"code\":\"SERIALIZATION_ERROR\",\"summary_status\":\"fail\",\"summary_text\":\"failed to serialize verification report: {err}\",\"transcript_encoding\":\"unknown\",\"receipt_profile\":\"unknown\",\"issuer\":\"unknown\",\"key_id\":\"unknown\",\"payload_digest_alg\":\"unknown\",\"payload_digest_hex\":\"unavailable\",\"signature_valid\":false,\"trusted_issuer\":false,\"revocation_checked\":false,\"revocation_ok\":false,\"policy_accepted\":false,\"verification_engine\":\"Rust ink-wasm\",\"network_required\":false,\"scope\":\"receipt-only\",\"checks\":[{{\"id\":\"artifacts.output\",\"status\":\"fail\",\"reason_code\":\"SERIALIZATION_ERROR\"}}]}}"
        )
    })
}

fn serialize_value(value: &Value, label: &str) -> Result<Vec<u8>, VerificationReportJson> {
    serde_json::to_vec(value).map_err(|err| {
        invalid_artifact_report(
            "ARTIFACT_SERIALIZATION_ERROR",
            &format!("Failed to serialize {label}: {err}"),
        )
    })
}

fn serialize_optional_value(
    value: Option<&Value>,
    label: &str,
) -> Result<Option<Vec<u8>>, VerificationReportJson> {
    value.map(|entry| serialize_value(entry, label)).transpose()
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen)]
pub fn verify_receipt(bytes: &[u8]) -> String {
    verify_receipt_with_policy(bytes, true)
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen)]
pub fn verify_receipt_with_policy(bytes: &[u8], allow_unsigned: bool) -> String {
    verify_receipt_with_context(bytes, allow_unsigned, None)
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen)]
pub fn verify_receipt_with_context(
    bytes: &[u8],
    allow_unsigned: bool,
    current_sequence: Option<u64>,
) -> String {
    verify_receipt_inner(bytes, allow_unsigned, current_sequence, &[])
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen)]
pub fn verify_receipt_with_trusted_key(
    bytes: &[u8],
    allow_unsigned: bool,
    issuer_id: &str,
    public_key_id: &str,
    public_key_hex: &str,
) -> String {
    verify_receipt_with_trusted_key_and_context(
        bytes,
        allow_unsigned,
        None,
        issuer_id,
        public_key_id,
        public_key_hex,
    )
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen)]
pub fn verify_receipt_with_trusted_key_and_context(
    bytes: &[u8],
    allow_unsigned: bool,
    current_sequence: Option<u64>,
    issuer_id: &str,
    public_key_id: &str,
    public_key_hex: &str,
) -> String {
    let public_key = match hex::decode(public_key_hex)
        .ok()
        .and_then(|value| value.try_into().ok())
    {
        Some(value) => value,
        None => return error_json("INVALID_TRUSTED_KEY"),
    };
    let issuer_id = match IssuerId::from_str(issuer_id) {
        Ok(value) => value,
        Err(_) => return error_json("INVALID_TRUSTED_KEY"),
    };
    let public_key_id = match PublicKeyId::from_str(public_key_id) {
        Ok(value) => value,
        Err(_) => return error_json("INVALID_TRUSTED_KEY"),
    };
    let trusted_key = TrustedIssuerKey {
        issuer_id,
        public_key_id,
        public_key: ink_core::Ed25519PublicKey(public_key),
    };
    verify_receipt_inner(bytes, allow_unsigned, current_sequence, &[trusted_key])
}

fn verify_receipt_inner(
    bytes: &[u8],
    allow_unsigned: bool,
    current_sequence: Option<u64>,
    trusted_keys: &[TrustedIssuerKey],
) -> String {
    match canon::decode_receipt(bytes)
        .map_err(|_| "DECODE_ERROR")
        .and_then(|receipt| {
            ink_verify::verify_receipt(
                &receipt,
                trusted_keys,
                VerificationPolicy {
                    allow_unsigned,
                    current_sequence,
                },
            )
            .map_err(|_| "VERIFY_ERROR")
        }) {
        Ok(report) => receipt_report_json(&report),
        Err(code) => error_json(code),
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen)]
pub fn verify_bundle(bytes: &[u8]) -> String {
    if !bytes.len().is_multiple_of(32) {
        return error_json("INVALID_BUNDLE_BYTES");
    }
    let mut bundle = ink_core::Bundle::new();
    for chunk in bytes.chunks(32) {
        let mut digest = [0u8; 32];
        digest.copy_from_slice(chunk);
        if bundle.add_receipt(ink_core::Digest(digest)).is_err() {
            return error_json("BUNDLE_TOO_LARGE");
        }
    }
    match bundle
        .seal()
        .map_err(|_| "BUNDLE_SEAL_ERROR")
        .and_then(|sealed| ink_verify::verify_bundle(&sealed).map_err(|_| "BUNDLE_VERIFY_ERROR"))
    {
        Ok(report) => format!(
            "{{\"valid\":{},\"receipt_count\":{}}}",
            report.valid, report.receipt_count
        ),
        Err(code) => error_json(code),
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen)]
pub fn compare_receipts(old_bytes: &[u8], new_bytes: &[u8]) -> String {
    match (
        canon::decode_receipt(old_bytes),
        canon::decode_receipt(new_bytes),
    ) {
        (Ok(left), Ok(right)) => match ink_core::compare::compare_receipts(&left, &right) {
            Ok(diff) => format!(
                "{{\"comparable\":{},\"same_hash\":{},\"kind\":\"{:?}\"}}",
                diff.comparable, diff.same_hash, diff.kind
            ),
            Err(_) => error_json("COMPARE_ERROR"),
        },
        _ => error_json("DECODE_ERROR"),
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen)]
pub fn replay_receipt(receipt_bytes: &[u8], _evidence_bytes: &[u8]) -> String {
    match canon::decode_receipt(receipt_bytes) {
        Ok(receipt) => format!(
            "{{\"replayable\":{}}}",
            receipt.body_hash != ink_core::Digest::zero()
        ),
        Err(_) => error_json("DECODE_ERROR"),
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen)]
pub fn verify_artifacts(input_json: &str) -> String {
    let input: ArtifactInput = match serde_json::from_str(input_json) {
        Ok(value) => value,
        Err(err) => {
            return render_artifact_report(&invalid_artifact_report(
                "INVALID_INPUT_JSON",
                &format!("Artifact payload must be valid JSON: {err}"),
            ));
        }
    };

    let Some(receipt) = input.receipt else {
        return render_artifact_report(&invalid_artifact_report(
            "RECEIPT_NOT_SUPPLIED",
            "Verification requires a portable ink.receipt.v2 artifact.",
        ));
    };

    let receipt_json = match serialize_value(&receipt, "receipt") {
        Ok(bytes) => bytes,
        Err(report) => return render_artifact_report(&report),
    };
    let manifest_json = match serialize_optional_value(input.manifest.as_ref(), "manifest") {
        Ok(bytes) => bytes,
        Err(report) => return render_artifact_report(&report),
    };
    let trust_registry_json =
        match serialize_optional_value(input.trust_registry.as_ref(), "trust registry") {
            Ok(bytes) => bytes,
            Err(report) => return render_artifact_report(&report),
        };
    let revocations_json = match serialize_optional_value(input.revocations.as_ref(), "revocations")
    {
        Ok(bytes) => bytes,
        Err(report) => return render_artifact_report(&report),
    };
    let verification_policy_json =
        match serialize_optional_value(input.verification_policy.as_ref(), "verification policy") {
            Ok(bytes) => bytes,
            Err(report) => return render_artifact_report(&report),
        };

    let result = ink_receipt_v2::verify_receipt(
        &receipt_json,
        manifest_json.as_deref(),
        None,
        trust_registry_json.as_deref(),
        revocations_json.as_deref(),
        verification_policy_json.as_deref(),
        None,
    );

    match result {
        Ok(report) => render_artifact_report(&report),
        Err(err) => render_artifact_report(&invalid_artifact_report(
            "VERIFY_ARTIFACTS_FAILED",
            &format!("Artifact verification failed: {err}"),
        )),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ink_vectors::{kernel_decode_vectors, kernel_verification_vectors};
    use serde_json::{json, Value};
    use std::fs;
    use std::path::Path;

    #[derive(Debug, Deserialize)]
    struct VectorFile {
        vectors: Vec<SharedVector>,
    }

    #[derive(Debug, Deserialize, Clone)]
    struct SharedVector {
        name: String,
        receipt: Value,
        manifest: Option<Value>,
        trust_registry: Option<Value>,
        verify_policy: Option<Value>,
        expect_status: String,
        expect_code: String,
    }

    fn public_vectors() -> Vec<SharedVector> {
        let path =
            Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../test-vectors/ink-vectors.json");
        let payload = fs::read(path).unwrap();
        serde_json::from_slice::<VectorFile>(&payload)
            .unwrap()
            .vectors
    }

    #[test]
    fn wasm_receipt_verification_matches_native_statuses() {
        for vector in kernel_verification_vectors() {
            let bytes = hex::decode(&vector.receipt_bytes_hex).unwrap();
            let receipt = ink_core::canon::decode_receipt(&bytes).unwrap();
            let native = ink_verify::verify_receipt(
                &receipt,
                &vector.trusted_keys,
                VerificationPolicy {
                    allow_unsigned: vector.allow_unsigned,
                    current_sequence: vector.current_sequence,
                },
            )
            .unwrap();
            let wasm_json = if let Some(trusted_key) = vector.trusted_keys.first() {
                verify_receipt_with_trusted_key_and_context(
                    &bytes,
                    vector.allow_unsigned,
                    vector.current_sequence,
                    trusted_key.issuer_id.as_str().unwrap(),
                    trusted_key.public_key_id.as_str().unwrap(),
                    &hex::encode(trusted_key.public_key.0),
                )
            } else {
                verify_receipt_with_context(&bytes, vector.allow_unsigned, vector.current_sequence)
            };
            let wasm: Value = serde_json::from_str(&wasm_json).unwrap();
            assert_eq!(
                wasm["structural_valid"], native.core.valid,
                "{}",
                vector.name
            );
            assert_eq!(wasm["status"], native.status.as_str(), "{}", vector.name);
            assert_eq!(wasm["code"], native.code.as_str(), "{}", vector.name);
        }
    }

    #[test]
    fn wasm_decode_errors_match_the_vector_contract() {
        for vector in kernel_decode_vectors() {
            let bytes = hex::decode(&vector.receipt_bytes_hex).unwrap();
            let wasm: Value = serde_json::from_str(&verify_receipt(&bytes)).unwrap();
            assert_eq!(wasm["status"], "error", "{}", vector.name);
            assert_eq!(wasm["code"], vector.expected_error, "{}", vector.name);
            assert!(
                ink_core::canon::decode_receipt(&bytes).is_err(),
                "{}",
                vector.name
            );
        }
    }

    #[test]
    fn verify_artifacts_matches_public_vector_statuses() {
        for vector in public_vectors() {
            let report: VerificationReportJson = serde_json::from_str(&verify_artifacts(
                &json!({
                    "receipt": vector.receipt,
                    "manifest": vector.manifest,
                    "trust_registry": vector.trust_registry,
                    "verification_policy": vector.verify_policy,
                })
                .to_string(),
            ))
            .unwrap();
            assert_eq!(report.status, vector.expect_status, "{}", vector.name);
            assert_eq!(report.code, vector.expect_code, "{}", vector.name);
            assert_eq!(
                report.summary_status,
                if report.status != "valid" {
                    "fail"
                } else if report
                    .checks
                    .iter()
                    .any(|check| check.status == "not_performed")
                {
                    "warning"
                } else {
                    "pass"
                },
                "{}",
                vector.name
            );
        }
    }

    #[test]
    fn verify_artifacts_reports_warning_when_optional_inputs_are_missing() {
        let vector = public_vectors()
            .into_iter()
            .find(|entry| entry.name == "valid_tlv_v2_trusted_manifest")
            .unwrap();
        let report: VerificationReportJson = serde_json::from_str(&verify_artifacts(
            &json!({
                "receipt": vector.receipt,
                "trust_registry": vector.trust_registry,
            })
            .to_string(),
        ))
        .unwrap();

        assert_eq!(report.status, "valid");
        assert_eq!(report.code, "VALID_RECEIPT");
        assert_eq!(report.summary_status, "warning");
    }

    #[test]
    fn verify_artifacts_returns_invalid_input_report_when_receipt_is_missing() {
        let report: VerificationReportJson =
            serde_json::from_str(&verify_artifacts("{\"manifest\":{}}")).unwrap();

        assert_eq!(report.status, "invalid");
        assert_eq!(report.code, "RECEIPT_NOT_SUPPLIED");
        assert_eq!(report.summary_status, "fail");
    }
}
