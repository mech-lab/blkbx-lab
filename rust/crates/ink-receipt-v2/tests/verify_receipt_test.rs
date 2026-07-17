use ink_receipt_v2::VerificationReportJson;
use serde::Deserialize;
use serde_json::Value;
use std::path::Path;

#[derive(Debug, Deserialize)]
struct VectorFile {
    vectors: Vec<SharedVector>,
}

#[derive(Debug, Deserialize)]
struct SharedVector {
    receipt: Value,
    manifest: Option<Value>,
    trust_registry: Option<Value>,
    verify_policy: Option<Value>,
    pinned_public_key: Option<String>,
    expect_status: String,
    expect_code: String,
}

#[test]
fn integration_vectors_match_the_public_contract() {
    let path = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../test-vectors/ink-vectors.json");
    let vectors: VectorFile = serde_json::from_slice(&std::fs::read(path).unwrap()).unwrap();
    for vector in &vectors.vectors {
        let report: VerificationReportJson = ink_receipt_v2::verify_receipt(
            &serde_json::to_vec(&vector.receipt).unwrap(),
            vector
                .manifest
                .as_ref()
                .map(|value| serde_json::to_vec(value).unwrap())
                .as_deref(),
            None,
            vector
                .trust_registry
                .as_ref()
                .map(|value| serde_json::to_vec(value).unwrap())
                .as_deref(),
            None,
            vector
                .verify_policy
                .as_ref()
                .map(|value| serde_json::to_vec(value).unwrap())
                .as_deref(),
            vector.pinned_public_key.as_deref(),
        )
        .unwrap();
        assert_eq!(report.status, vector.expect_status);
        assert_eq!(report.code, vector.expect_code);
    }
}
