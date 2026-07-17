#![forbid(unsafe_code)]

use ink_core::canon;
#[cfg(target_arch = "wasm32")]
use wasm_bindgen::prelude::*;

fn report_json(valid: bool, details: &str) -> String {
    format!("{{\"valid\":{},\"details\":\"{}\"}}", valid, details)
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen)]
pub fn verify_receipt(bytes: &[u8]) -> String {
    match canon::decode_receipt(bytes)
        .and_then(|receipt| ink_verify::verify_receipt(&receipt).map(|report| report.core.valid))
    {
        Ok(valid) => report_json(valid, "receipt"),
        Err(err) => report_json(false, &format!("error:{err}")),
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen)]
pub fn verify_bundle(bytes: &[u8]) -> String {
    if bytes.len() % 32 != 0 {
        return report_json(false, "error:invalid_bundle_bytes");
    }
    let mut bundle = ink_core::Bundle::new();
    for chunk in bytes.chunks(32) {
        let mut digest = [0u8; 32];
        digest.copy_from_slice(chunk);
        if bundle.add_receipt(ink_core::Digest(digest)).is_err() {
            return report_json(false, "error:bundle_too_large");
        }
    }
    match bundle
        .seal()
        .and_then(|sealed| ink_verify::verify_bundle(&sealed))
    {
        Ok(report) => report_json(report.valid, "bundle"),
        Err(err) => report_json(false, &format!("error:{err}")),
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
            Err(err) => report_json(false, &format!("error:{err}")),
        },
        (Err(err), _) | (_, Err(err)) => report_json(false, &format!("error:{err}")),
    }
}

#[cfg_attr(target_arch = "wasm32", wasm_bindgen)]
pub fn replay_receipt(receipt_bytes: &[u8], _evidence_bytes: &[u8]) -> String {
    match canon::decode_receipt(receipt_bytes) {
        Ok(receipt) => report_json(
            receipt.canonical_hash != ink_core::Digest::zero(),
            "receipt",
        ),
        Err(err) => report_json(false, &format!("error:{err}")),
    }
}
