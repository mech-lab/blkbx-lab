use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process;
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

use serde_json::json;

use super::{create_manifest, doctor, gate, verify, HostError};
use crate::digest_json;
use inkreceipts_core::digest::sha256;

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
