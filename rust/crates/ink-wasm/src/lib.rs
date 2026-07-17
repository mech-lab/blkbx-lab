#![forbid(unsafe_code)]

use ink_core::bounded::{IssuerId, PublicKeyId};
use ink_core::canon;
use ink_verify::TrustedIssuerKey;
use ink_verify::{ReceiptVerificationReport, VerificationPolicy};
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

#[cfg(test)]
mod tests {
    use super::*;
    use ink_vectors::{kernel_decode_vectors, kernel_verification_vectors};
    use serde_json::Value;

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
}
