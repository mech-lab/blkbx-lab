use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process;
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

use base64ct::{Base64UrlUnpadded, Encoding};
use ed25519_dalek::{Signer, SigningKey};
use serde_json::json;

use super::{
    create_manifest, doctor, gate, key_id_for_public, load_signer_config,
    receipt_digest_for_encoding, receipt_payload_from_json, revocation_list_digest, verify,
    HostError, LegacyTrustPolicyJson, LegacyTrustedKeyJson, ReceiptJson, RevocationListJson,
    RevokedKeyJson, SignerConfigJson, TrustRegistryJson, ACTIVE_PUBLIC_FILE, ACTIVE_SECRET_FILE,
    LEGACY_TRUST_POLICY_FILE, RECEIPT_ENCODING_JSON_CANONICAL_V1, RECEIPT_ENCODING_TLV_V1_LEGACY,
    RECEIPT_ENCODING_TLV_V2, REVOCATION_LIST_FILE, SIGNER_CONFIG_FILE, TRUST_REGISTRY_FILE,
};
use crate::digest_json;
use ink_core::digest::sha256;

static ENV_LOCK: Mutex<()> = Mutex::new(());

fn unique_temp_dir(prefix: &str) -> PathBuf {
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    env::temp_dir().join(format!("{prefix}-{}-{nanos}", process::id()))
}

fn write_bundle(root: &Path) {
    fs::create_dir_all(root).unwrap();

    let prompt = "Draft a low-risk status update for a routine claim.";
    fs::write(root.join("prompt.txt"), prompt).unwrap();
    let prompt_hash = digest_json(&sha256(prompt.as_bytes()));
    let action = json!({
        "schema": "ink.action.v1",
        "operation": "draft_status_update",
        "risk_class": "low",
        "human_review_requested": false,
        "prompt_hash": prompt_hash,
        "scenario_id": "low_risk_status_update",
        "matched_rule_ids": ["default.low"],
    });
    fs::write(
        root.join("action.json"),
        serde_json::to_vec_pretty(&action).unwrap(),
    )
    .unwrap();

    let schema_hash = digest_json(&sha256(b"ink.action.v1"));
    let model = json!({
        "schema": "ink.model-waist.v1",
        "identity": {
            "model_class": "deterministic_demo",
            "model_ref_hash": digest_json(&sha256(b"blkbx-lab:qwen35:deterministic-demo")),
            "model_slug": "qwen35-demo",
            "identity_evidence": {"kind": "declared"},
        },
        "invocation": {
            "action_hash": digest_json(&sha256(serde_json::to_string(&action).unwrap().as_bytes())),
            "messages_hash": prompt_hash,
            "system_prompt_hash": serde_json::Value::Null,
            "tool_spec_hash": serde_json::Value::Null,
            "response_schema_hash": schema_hash,
            "parameters_hash": digest_json(&sha256(b"params")),
            "requested_output": {
                "kind": "json_schema",
                "schema_hash": schema_hash,
            },
        },
        "observation": {
            "output_text_hash": digest_json(&sha256(b"demo-output")),
            "structured_output_hash": serde_json::Value::Null,
            "provider_metadata_hash": digest_json(&sha256(b"demo-metadata")),
            "finish_reason": "stop",
            "usage": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
            },
        },
        "runtime": {
            "runtime_kind": "deterministic_demo",
            "execution_topology": "rule_based_local",
            "replay_strength": "fully_replayable",
            "determinism": {"deterministic": true, "seed_bound": true},
            "isolation": {"process_isolated": true},
            "provider_routing": {
                "fallbacks_allowed": false,
                "provider_pinned": true,
                "data_collection_policy": "declared_deny",
            },
        },
        "plugin": {
            "plugin_id_hash": digest_json(&sha256(b"qwen35")),
            "plugin_version_hash": digest_json(&sha256(b"v1")),
            "plugin_api_version": "v1",
            "maintainer_class": "first_party_reference",
            "normalization": {
                "input_normalized": true,
                "output_normalized": true,
                "raw_request_preserved": true,
                "raw_response_preserved": true,
                "secrets_redacted": true,
            },
            "plugin_manifest_hash": digest_json(&sha256(b"blkbx-lab:deterministic-demo")),
            "plugin_id_hint": "qwen35",
            "trust_level": "first_party_reference",
        },
    });
    fs::write(
        root.join("model_waist.json"),
        serde_json::to_vec_pretty(&model).unwrap(),
    )
    .unwrap();
}

fn policy_path() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../policies/demo-claims.v1.json")
}

fn write_manifest_fixture(root: &Path, action_id: &str) -> PathBuf {
    let artifacts = json!([
        {
            "artifact_type": "prompt_text",
            "path": "prompt.txt",
            "media_type": "text/plain; charset=utf-8",
        },
        {
            "artifact_type": "action_json",
            "path": "action.json",
            "media_type": "application/json",
            "schema_id": "ink.action.v1",
        },
        {
            "artifact_type": "model_waist_json",
            "path": "model_waist.json",
            "media_type": "application/json",
            "schema_id": "ink.model-waist.v1",
        }
    ]);
    let manifest = create_manifest(
        root,
        action_id,
        &serde_json::to_string(&artifacts).unwrap(),
        Some("2026-07-13T00:00:00Z"),
    )
    .unwrap();
    PathBuf::from(manifest["manifest_path"].as_str().unwrap())
}

#[test]
fn host_gate_still_emits_v2_receipt_semantics_with_hardened_core() {
    let _guard = ENV_LOCK.lock().unwrap();
    let root = unique_temp_dir("inkreceipts-host-regression");
    let config = root.join("config");
    env::set_var("INKRECEIPTS_CONFIG_DIR", &config);
    fs::create_dir_all(&root).unwrap();
    doctor(true).unwrap();
    write_bundle(&root);

    let artifacts = json!([
        {
            "artifact_type": "prompt_text",
            "path": "prompt.txt",
            "media_type": "text/plain; charset=utf-8",
        },
        {
            "artifact_type": "action_json",
            "path": "action.json",
            "media_type": "application/json",
            "schema_id": "ink.action.v1",
        },
        {
            "artifact_type": "model_waist_json",
            "path": "model_waist.json",
            "media_type": "application/json",
            "schema_id": "ink.model-waist.v1",
        }
    ]);

    let manifest = create_manifest(
        &root,
        "urn:ink:action:host-regression",
        &serde_json::to_string(&artifacts).unwrap(),
        Some("2026-07-13T00:00:00Z"),
    )
    .unwrap();
    let manifest_path = PathBuf::from(manifest["manifest_path"].as_str().unwrap());
    let policy_path =
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../policies/demo-claims.v1.json");

    let gated = gate(&manifest_path, &policy_path, None, None, true).unwrap();
    assert_eq!(gated["decision"], "pass");

    let receipt_path = PathBuf::from(gated["receipt_path"].as_str().unwrap());
    let receipt: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(&receipt_path).unwrap()).unwrap();
    assert_eq!(receipt["schema"], "ink.receipt.v2");
    assert_eq!(receipt["runtime"]["runtime_kind"], "deterministic_demo");
    assert_eq!(receipt["decision"], "pass");
    assert_eq!(
        receipt["reason_codes"],
        json!(["RUNTIME_DETERMINISTIC_DEMO"])
    );

    let verified = verify(&receipt_path, Some(&manifest_path)).unwrap();
    assert_eq!(verified["verification"]["overall"], "pass");
    assert_eq!(verified["verification"]["scope"], "full-evidence");
    assert!(verified["verification"]["checks"]
        .as_array()
        .unwrap()
        .iter()
        .any(|check| check["id"] == "kernel.projection" && check["status"] == "pass"));

    let _ = fs::remove_dir_all(&root);
}

#[test]
fn host_gate_requires_explicit_demo_signer() {
    let _guard = ENV_LOCK.lock().unwrap();
    let root = unique_temp_dir("inkreceipts-host-requires-demo-signer");
    let config = root.join("config");
    env::set_var("INKRECEIPTS_CONFIG_DIR", &config);
    write_bundle(&root);

    let artifacts = json!([
        {
            "artifact_type": "prompt_text",
            "path": "prompt.txt",
            "media_type": "text/plain; charset=utf-8",
        },
        {
            "artifact_type": "action_json",
            "path": "action.json",
            "media_type": "application/json",
            "schema_id": "ink.action.v1",
        },
        {
            "artifact_type": "model_waist_json",
            "path": "model_waist.json",
            "media_type": "application/json",
            "schema_id": "ink.model-waist.v1",
        }
    ]);
    let manifest = create_manifest(
        &root,
        "urn:ink:action:host-demo-signer",
        &serde_json::to_string(&artifacts).unwrap(),
        Some("2026-07-13T00:00:00Z"),
    )
    .unwrap();
    let manifest_path = PathBuf::from(manifest["manifest_path"].as_str().unwrap());
    let policy_path =
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../policies/demo-claims.v1.json");

    let result = gate(&manifest_path, &policy_path, None, None, false);
    assert!(matches!(result, Err(HostError::Trust(message)) if message.contains("demo signer")));

    let _ = fs::remove_dir_all(&root);
}

#[test]
fn host_verify_rejects_mismatched_runtime_projection() {
    let _guard = ENV_LOCK.lock().unwrap();
    let root = unique_temp_dir("inkreceipts-host-runtime-projection");
    let config = root.join("config");
    env::set_var("INKRECEIPTS_CONFIG_DIR", &config);
    fs::create_dir_all(&root).unwrap();
    doctor(true).unwrap();
    write_bundle(&root);

    let artifacts = json!([
        {
            "artifact_type": "prompt_text",
            "path": "prompt.txt",
            "media_type": "text/plain; charset=utf-8",
        },
        {
            "artifact_type": "action_json",
            "path": "action.json",
            "media_type": "application/json",
            "schema_id": "ink.action.v1",
        },
        {
            "artifact_type": "model_waist_json",
            "path": "model_waist.json",
            "media_type": "application/json",
            "schema_id": "ink.model-waist.v1",
        }
    ]);
    let manifest = create_manifest(
        &root,
        "urn:ink:action:host-runtime-projection",
        &serde_json::to_string(&artifacts).unwrap(),
        Some("2026-07-13T00:00:00Z"),
    )
    .unwrap();
    let manifest_path = PathBuf::from(manifest["manifest_path"].as_str().unwrap());
    let policy_path =
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../policies/demo-claims.v1.json");

    let gated = gate(&manifest_path, &policy_path, None, None, true).unwrap();
    let receipt_path = PathBuf::from(gated["receipt_path"].as_str().unwrap());
    let mut receipt: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(&receipt_path).unwrap()).unwrap();
    receipt["runtime"]["runtime_kind"] = json!("hosted_model_api");
    fs::write(&receipt_path, serde_json::to_vec_pretty(&receipt).unwrap()).unwrap();

    let verified = verify(&receipt_path, Some(&manifest_path));
    assert!(
        matches!(verified, Err(HostError::InvalidInput(message)) if message.contains("runtime projection"))
    );

    let _ = fs::remove_dir_all(&root);
}

#[test]
fn host_gate_rejects_verify_only_receipt_encodings() {
    let _guard = ENV_LOCK.lock().unwrap();
    let root = unique_temp_dir("inkreceipts-host-file-signer");
    let config_root = root.join("config");
    env::set_var("INKRECEIPTS_CONFIG_DIR", &config_root);
    fs::create_dir_all(&root).unwrap();
    doctor(true).unwrap();
    write_bundle(&root);
    let manifest_path = write_manifest_fixture(&root, "urn:ink:action:file-signer");

    let signer_path = config_root.join(SIGNER_CONFIG_FILE);
    for encoding in [
        RECEIPT_ENCODING_TLV_V1_LEGACY,
        RECEIPT_ENCODING_JSON_CANONICAL_V1,
    ] {
        let mut signer: SignerConfigJson =
            serde_json::from_str(&fs::read_to_string(&signer_path).unwrap()).unwrap();
        signer.backend = "file_ed25519".to_string();
        signer.receipt_encoding = encoding.to_string();
        fs::write(&signer_path, serde_json::to_vec_pretty(&signer).unwrap()).unwrap();

        let doc = doctor(false).unwrap();
        assert_eq!(doc["demo_ready"], json!(false));
        assert_eq!(doc["real_replay_ready"], json!(false));
        assert!(doc["checks"].as_array().unwrap().iter().any(|check| {
            check["name"] == "receipt_encoding"
                && check["status"] == "verify_only"
                && check["encoding"] == json!(encoding)
        }));

        let gated = gate(&manifest_path, &policy_path(), None, None, false);
        assert!(
            matches!(gated, Err(HostError::InvalidInput(message)) if message.contains("verify-only compatibility mode")
                && message.contains(RECEIPT_ENCODING_TLV_V2))
        );
    }

    let _ = fs::remove_dir_all(&root);
}

#[test]
fn host_verify_accepts_json_canonical_compat_receipts() {
    let _guard = ENV_LOCK.lock().unwrap();
    let root = unique_temp_dir("inkreceipts-host-json-canonical-compat");
    let config_root = root.join("config");
    env::set_var("INKRECEIPTS_CONFIG_DIR", &config_root);
    fs::create_dir_all(&root).unwrap();
    doctor(true).unwrap();
    write_bundle(&root);

    let signer_path = config_root.join(SIGNER_CONFIG_FILE);
    let mut signer: SignerConfigJson =
        serde_json::from_str(&fs::read_to_string(&signer_path).unwrap()).unwrap();
    signer.backend = "file_ed25519".to_string();
    signer.receipt_encoding = RECEIPT_ENCODING_TLV_V2.to_string();
    fs::write(&signer_path, serde_json::to_vec_pretty(&signer).unwrap()).unwrap();

    let manifest_path = write_manifest_fixture(&root, "urn:ink:action:json-canonical-compat");
    let gated = gate(&manifest_path, &policy_path(), None, None, false).unwrap();
    let receipt_path = PathBuf::from(gated["receipt_path"].as_str().unwrap());
    let mut receipt: ReceiptJson =
        serde_json::from_str(&fs::read_to_string(&receipt_path).unwrap()).unwrap();

    let signer = load_signer_config().unwrap();
    let secret_key_text = fs::read_to_string(config_root.join(&signer.secret_key_path)).unwrap();
    let secret_key_bytes = Base64UrlUnpadded::decode_vec(secret_key_text.trim()).unwrap();
    let signing_key = SigningKey::from_bytes(&secret_key_bytes.try_into().unwrap());

    receipt.signing.transcript_encoding = RECEIPT_ENCODING_JSON_CANONICAL_V1.to_string();
    let payload = receipt_payload_from_json(&receipt).unwrap();
    let digest =
        receipt_digest_for_encoding(&receipt, &payload, RECEIPT_ENCODING_JSON_CANONICAL_V1)
            .unwrap();
    receipt.signing.payload_hash = digest_json(&digest);
    receipt.signing.signature =
        Base64UrlUnpadded::encode_string(&signing_key.sign(&digest.0).to_bytes());
    fs::write(&receipt_path, serde_json::to_vec_pretty(&receipt).unwrap()).unwrap();

    let verified = verify(&receipt_path, Some(&manifest_path)).unwrap();
    assert_eq!(verified["verification"]["overall"], "pass");

    let _ = fs::remove_dir_all(&root);
}

#[test]
fn host_verify_rejects_revoked_keys() {
    let _guard = ENV_LOCK.lock().unwrap();
    let root = unique_temp_dir("inkreceipts-host-revocation");
    let config_root = root.join("config");
    env::set_var("INKRECEIPTS_CONFIG_DIR", &config_root);
    fs::create_dir_all(&root).unwrap();
    doctor(true).unwrap();
    write_bundle(&root);

    let manifest_path = write_manifest_fixture(&root, "urn:ink:action:revoked-key");
    let gated = gate(&manifest_path, &policy_path(), None, None, true).unwrap();
    let receipt_path = PathBuf::from(gated["receipt_path"].as_str().unwrap());

    let signer = load_signer_config().unwrap();
    let secret_key_text = fs::read_to_string(config_root.join(&signer.secret_key_path)).unwrap();
    let secret_key_bytes = Base64UrlUnpadded::decode_vec(secret_key_text.trim()).unwrap();
    let signing_key = SigningKey::from_bytes(&secret_key_bytes.try_into().unwrap());

    let revocation_path = config_root.join(REVOCATION_LIST_FILE);
    let mut list: RevocationListJson =
        serde_json::from_str(&fs::read_to_string(&revocation_path).unwrap()).unwrap();
    list.revoked_keys.push(RevokedKeyJson {
        key_id: signer.key_id.clone(),
        reason: "compromised_for_test".to_string(),
        revoked_at: "2026-07-16T00:00:00Z".to_string(),
    });
    let digest = revocation_list_digest(&list).unwrap();
    list.signing.payload_hash = digest_json(&digest);
    list.signing.signature =
        Base64UrlUnpadded::encode_string(&signing_key.sign(&digest.0).to_bytes());
    fs::write(&revocation_path, serde_json::to_vec_pretty(&list).unwrap()).unwrap();

    let verified = verify(&receipt_path, Some(&manifest_path));
    assert!(matches!(verified, Err(HostError::Trust(message)) if message.contains("revoked")));

    let _ = fs::remove_dir_all(&root);
}

#[test]
fn doctor_migrates_legacy_trust_policy_into_current_config() {
    let _guard = ENV_LOCK.lock().unwrap();
    let root = unique_temp_dir("inkreceipts-host-legacy-migration");
    let config_root = root.join("config");
    let keys_root = config_root.join("keys");
    env::set_var("INKRECEIPTS_CONFIG_DIR", &config_root);
    fs::create_dir_all(&keys_root).unwrap();

    let secret_key = [7u8; 32];
    let signing_key = SigningKey::from_bytes(&secret_key);
    let public_key = signing_key.verifying_key().to_bytes();
    let key_id = key_id_for_public(&public_key);
    fs::write(
        keys_root.join(ACTIVE_SECRET_FILE),
        Base64UrlUnpadded::encode_string(&secret_key),
    )
    .unwrap();
    fs::write(
        keys_root.join(ACTIVE_PUBLIC_FILE),
        Base64UrlUnpadded::encode_string(&public_key),
    )
    .unwrap();

    let legacy = LegacyTrustPolicyJson {
        schema: "ink.trust-policy.v1".to_string(),
        trusted_keys: vec![LegacyTrustedKeyJson {
            key_id: key_id.clone(),
            algorithm: "Ed25519".to_string(),
            public_key: Base64UrlUnpadded::encode_string(&public_key),
            issuer_names: vec!["Legacy Issuer".to_string()],
            status: "active".to_string(),
        }],
    };
    fs::write(
        config_root.join(LEGACY_TRUST_POLICY_FILE),
        serde_json::to_vec_pretty(&legacy).unwrap(),
    )
    .unwrap();

    let doc = doctor(true).unwrap();
    assert_eq!(doc["status"], "ready");
    assert!(config_root.join(SIGNER_CONFIG_FILE).exists());
    assert!(config_root.join(TRUST_REGISTRY_FILE).exists());
    assert!(config_root.join(REVOCATION_LIST_FILE).exists());

    let signer: SignerConfigJson =
        serde_json::from_str(&fs::read_to_string(config_root.join(SIGNER_CONFIG_FILE)).unwrap())
            .unwrap();
    assert_eq!(signer.key_id, key_id);
    assert_eq!(signer.issuer_name, "Legacy Issuer");

    let registry: TrustRegistryJson =
        serde_json::from_str(&fs::read_to_string(config_root.join(TRUST_REGISTRY_FILE)).unwrap())
            .unwrap();
    assert!(registry
        .issuers
        .iter()
        .any(|entry| entry.key_id == key_id && entry.issuer_name == "Legacy Issuer"));

    let _ = fs::remove_dir_all(&root);
}
