use base64ct::{Base64UrlUnpadded, Encoding};
use ed25519_dalek::{Signer, SigningKey};
use ink_core::digest::sha256;
use ink_receipt_v2::VerificationReportJson;
use serde::Deserialize;
use serde_json::{json, Value};
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

#[test]
fn retired_v2_trusted_issuer_still_verifies() {
    let vector = shared_vector(0);
    let receipt = vector.receipt;
    let manifest = vector.manifest.expect("manifest");
    let trust_secret = [9u8; 32];
    let trust_signing_key = SigningKey::from_bytes(&trust_secret);
    let trust_public_key =
        Base64UrlUnpadded::encode_string(&trust_signing_key.verifying_key().to_bytes());
    let trust_key_id = "trust-authority-v2";

    let registry = sign_document(
        json!({
            "schema": "ink.trust-registry.v2",
            "registry_version": "2026-07-18.1",
            "published_at": "2026-07-18T00:00:00Z",
            "trust_authorities": [
                {
                    "key_id": trust_key_id,
                    "algorithm": "Ed25519",
                    "public_key": trust_public_key,
                    "state": "active"
                }
            ],
            "issuers": [
                {
                    "key_id": receipt["signing"]["key_id"],
                    "algorithm": "Ed25519",
                    "public_key": receipt["issuer"]["public_key"],
                    "issuer_name": receipt["issuer"]["name"],
                    "org_name": "BLKBX Lab",
                    "usage": "receipt_signing",
                    "state": "retired",
                    "valid_from": "2026-07-01T00:00:00Z"
                }
            ]
        }),
        &trust_secret,
        trust_key_id,
        "INK-TRUST-REGISTRY-JSON-V2",
    );
    let revocations = sign_document(
        json!({
            "schema": "ink.revocations.v2",
            "list_version": "2026-07-18.1",
            "published_at": "2026-07-18T00:00:00Z",
            "revoked_keys": []
        }),
        &trust_secret,
        trust_key_id,
        "INK-REVOCATION-JSON-V2",
    );

    let report = ink_receipt_v2::verify_receipt(
        &serde_json::to_vec(&receipt).unwrap(),
        Some(&serde_json::to_vec(&manifest).unwrap()),
        None,
        Some(&serde_json::to_vec(&registry).unwrap()),
        Some(&serde_json::to_vec(&revocations).unwrap()),
        None,
        None,
    )
    .unwrap();

    assert_eq!(report.status, "valid");
    assert_eq!(report.code, "VALID_RECEIPT");
}

#[test]
fn revoked_v2_trusted_issuer_fails_verification() {
    let vector = shared_vector(0);
    let receipt = vector.receipt;
    let manifest = vector.manifest.expect("manifest");
    let trust_secret = [11u8; 32];
    let trust_signing_key = SigningKey::from_bytes(&trust_secret);
    let trust_public_key =
        Base64UrlUnpadded::encode_string(&trust_signing_key.verifying_key().to_bytes());
    let trust_key_id = "trust-authority-v2";

    let registry = sign_document(
        json!({
            "schema": "ink.trust-registry.v2",
            "registry_version": "2026-07-18.2",
            "published_at": "2026-07-18T00:00:00Z",
            "trust_authorities": [
                {
                    "key_id": trust_key_id,
                    "algorithm": "Ed25519",
                    "public_key": trust_public_key,
                    "state": "active"
                }
            ],
            "issuers": [
                {
                    "key_id": receipt["signing"]["key_id"],
                    "algorithm": "Ed25519",
                    "public_key": receipt["issuer"]["public_key"],
                    "issuer_name": receipt["issuer"]["name"],
                    "org_name": "BLKBX Lab",
                    "usage": "receipt_signing",
                    "state": "active",
                    "valid_from": "2026-07-01T00:00:00Z"
                }
            ]
        }),
        &trust_secret,
        trust_key_id,
        "INK-TRUST-REGISTRY-JSON-V2",
    );
    let revocations = sign_document(
        json!({
            "schema": "ink.revocations.v2",
            "list_version": "2026-07-18.2",
            "published_at": "2026-07-18T00:00:00Z",
            "revoked_keys": [
                {
                    "key_id": receipt["signing"]["key_id"],
                    "reason": "compromised_for_test",
                    "revoked_at": "2026-07-18T00:00:00Z"
                }
            ]
        }),
        &trust_secret,
        trust_key_id,
        "INK-REVOCATION-JSON-V2",
    );

    let report = ink_receipt_v2::verify_receipt(
        &serde_json::to_vec(&receipt).unwrap(),
        Some(&serde_json::to_vec(&manifest).unwrap()),
        None,
        Some(&serde_json::to_vec(&registry).unwrap()),
        Some(&serde_json::to_vec(&revocations).unwrap()),
        None,
        None,
    )
    .unwrap();

    assert_eq!(report.status, "invalid");
    assert_eq!(report.code, "REVOKED_ISSUER_KEY");
}

fn shared_vector(index: usize) -> SharedVector {
    let path = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../test-vectors/ink-vectors.json");
    let vectors: VectorFile = serde_json::from_slice(&std::fs::read(path).unwrap()).unwrap();
    vectors.vectors.into_iter().nth(index).unwrap()
}

fn sign_document(
    mut value: Value,
    secret_key: &[u8; 32],
    key_id: &str,
    transcript_encoding: &str,
) -> Value {
    let digest = sha256(&canonicalize_without_signing(&value));
    let signing_key = SigningKey::from_bytes(secret_key);
    value["signing"] = json!({
        "transcript_encoding": transcript_encoding,
        "payload_hash": {
            "algorithm": "sha-256",
            "digest": hex::encode(digest.0)
        },
        "algorithm": "Ed25519",
        "key_id": key_id,
        "signature": Base64UrlUnpadded::encode_string(&signing_key.sign(&digest.0).to_bytes())
    });
    value
}

fn canonicalize_without_signing(value: &Value) -> Vec<u8> {
    let mut value = value.clone();
    if let Some(map) = value.as_object_mut() {
        map.remove("signing");
    }
    canonicalize(&value)
}

fn canonicalize(value: &Value) -> Vec<u8> {
    match value {
        Value::Null => b"null".to_vec(),
        Value::Bool(value) => {
            if *value {
                b"true".to_vec()
            } else {
                b"false".to_vec()
            }
        }
        Value::Number(number) => number.to_string().into_bytes(),
        Value::String(string) => serde_json::to_string(string).unwrap().into_bytes(),
        Value::Array(items) => {
            let mut out = vec![b'['];
            for (index, item) in items.iter().enumerate() {
                if index > 0 {
                    out.push(b',');
                }
                out.extend_from_slice(&canonicalize(item));
            }
            out.push(b']');
            out
        }
        Value::Object(map) => {
            let mut entries = map.iter().collect::<Vec<_>>();
            entries.sort_by(|left, right| left.0.cmp(right.0));
            let mut out = vec![b'{'];
            for (index, (key, value)) in entries.iter().enumerate() {
                if index > 0 {
                    out.push(b',');
                }
                out.extend_from_slice(serde_json::to_string(key).unwrap().as_bytes());
                out.push(b':');
                out.extend_from_slice(&canonicalize(value));
            }
            out.push(b'}');
            out
        }
    }
}
