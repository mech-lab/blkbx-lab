use std::collections::BTreeMap;
use std::env;
use std::fs::{self, File};
use std::io::Write;
use std::path::{Component, Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use base64ct::{Base64UrlUnpadded, Encoding};
use chrono::{SecondsFormat, TimeZone, Utc};
use dirs::config_dir;
use ed25519_dalek::{Signer, SigningKey};
use ink_core::bounded::{DomainTag, IssuerId, SchemaAuthority, SchemaId};
use ink_core::controls::{ControlObservation, ControlSet, ControlStatus, ControlType};
use ink_core::digest::{sha256, write_tlv, Sha256Sink};
use ink_core::legacy::compare::{compare_receipts, ComparisonOut, VerifiedReceiptSummary};
use ink_core::legacy::policy::{
    evaluate_policy, CompiledPolicy, CompiledRule, ConditionNode, ConditionOp, ConditionValue,
    Decision, EvaluationOut, PluginTrustFact, PolicyFacts, PolicyInput, ReasonCodeSlot,
    ReasonWriter, RiskClass, RuleEffect,
};
use ink_core::legacy::receipt::{
    build_receipt_payload, receipt_transcript_hash, receipt_transcript_hash_legacy_v1, IssuerClaim,
    PolicyBinding, ReceiptInput, ReceiptPayload, ReceiptProfile, ReceiptSchemaVersion,
};
use ink_core::limits;
use ink_core::manifest::{ArtifactRef, ArtifactType, ManifestBinding, MediaType};
use ink_core::model_waist::{
    DataCollectionPolicy, DeterminismClaim, ExecutionTopology, FinishReason, IdentityEvidence,
    IsolationClaim, MaintainerClass, ModelClass, ModelIdentityClaim, ModelInvocationClaim,
    ModelObservationClaim, ModelWaist, NormalizationClaim, PluginApiVersion, PluginClaim,
    PluginTrustLevel, ProviderRoutingClaim, ReplayStrength, RequestedOutput, RuntimeClaim,
    RuntimeKind, TokenUsage,
};
use ink_core::types::{
    ActionId, BoundedBytes, Ed25519PublicKey, Ed25519Signature, KeyId, ReceiptId, Sha256Digest,
    TimestampUtc,
};
use ink_core::{Digest as KernelDigest, ReceiptEnvelope};
use ink_verify::verify_ed25519_message_hash_bytes;
use rand::RngCore;
use reqwest::blocking::Client;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256, Sha512};
use thiserror::Error;

const LOCAL_ISSUER_NAME: &str = "BLKBX Local Dev";
const RECEIPT_PROFILE: &str = "thin_waist_v2";
const LEGACY_DEV_SECRET: &[u8] = b"dev-secret-key-do-not-use-in-prod";
const CONFIG_DIR_NAME: &str = "inkreceipts";
const LEGACY_TRUST_POLICY_FILE: &str = "trust-policy.json";
const SIGNER_CONFIG_FILE: &str = "signer-config.json";
const TRUST_REGISTRY_FILE: &str = "trust-registry.json";
const REVOCATION_LIST_FILE: &str = "revocations.json";
const ACTIVE_SECRET_FILE: &str = "active.ed25519.key";
const ACTIVE_PUBLIC_FILE: &str = "active.ed25519.pub";
const RECEIPT_ENCODING_TLV_V2: &str = "INK-CORE-TLV-V2";
const RECEIPT_ENCODING_TLV_V1_LEGACY: &str = "INK-CORE-TRANSCRIPT-V1";
const RECEIPT_ENCODING_JSON_CANONICAL_V1: &str = "INK-CORE-JSON-CANONICAL-V1";
const REVOCATION_ENCODING_JSON_V1: &str = "INK-REVOCATION-JSON-V1";

#[derive(Debug, Error)]
pub enum HostError {
    #[error("io error: {0}")]
    Io(#[from] std::io::Error),
    #[error("json error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("http error: {0}")]
    Http(#[from] reqwest::Error),
    #[error("core error: {0:?}")]
    Core(ink_core::error::Error),
    #[error("invalid input: {0}")]
    InvalidInput(String),
    #[error("unsafe path: {0}")]
    UnsafePath(String),
    #[error("trust error: {0}")]
    Trust(String),
}

impl From<ink_core::error::Error> for HostError {
    fn from(value: ink_core::error::Error) -> Self {
        Self::Core(value)
    }
}

fn receipt_encoding_allows_issuance(encoding: &str) -> bool {
    encoding == RECEIPT_ENCODING_TLV_V2
}

fn receipt_encoding_check(encoding: &str) -> Value {
    let status = match encoding {
        RECEIPT_ENCODING_TLV_V2 => "ok",
        RECEIPT_ENCODING_TLV_V1_LEGACY | RECEIPT_ENCODING_JSON_CANONICAL_V1 => "verify_only",
        _ => "unsupported",
    };
    json!({
        "name": "receipt_encoding",
        "status": status,
        "encoding": encoding,
    })
}

fn receipt_encoding_note(encoding: &str) -> Option<String> {
    match encoding {
        RECEIPT_ENCODING_TLV_V2 => None,
        RECEIPT_ENCODING_TLV_V1_LEGACY | RECEIPT_ENCODING_JSON_CANONICAL_V1 => Some(format!(
            "receipt encoding {encoding} is verify-only compatibility mode; new receipts must use {RECEIPT_ENCODING_TLV_V2}"
        )),
        other => Some(format!(
            "receipt encoding {other} is unsupported; new receipts must use {RECEIPT_ENCODING_TLV_V2}"
        )),
    }
}

fn ensure_issueable_receipt_encoding(encoding: &str) -> Result<(), HostError> {
    if receipt_encoding_allows_issuance(encoding) {
        return Ok(());
    }
    Err(HostError::InvalidInput(
        receipt_encoding_note(encoding)
            .unwrap_or_else(|| format!("new receipts must use {RECEIPT_ENCODING_TLV_V2}")),
    ))
}

#[derive(Debug, Deserialize)]
pub struct ManifestArtifactSpec {
    pub artifact_type: String,
    pub path: String,
    pub media_type: String,
    pub schema_id: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DigestJson {
    pub algorithm: String,
    pub digest: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct SchemaJson {
    id: String,
    version: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct ManifestArtifactJson {
    artifact_type: String,
    path: String,
    media_type: String,
    size_bytes: u64,
    hash: DigestJson,
    #[serde(skip_serializing_if = "Option::is_none")]
    schema: Option<SchemaJson>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct ManifestJson {
    schema: String,
    action_id: String,
    created_at: String,
    artifacts: Vec<ManifestArtifactJson>,
}

#[allow(dead_code)]
#[derive(Debug, Deserialize)]
struct ActionJson {
    schema: String,
    operation: String,
    risk_class: String,
    human_review_requested: bool,
    prompt_hash: DigestJson,
    scenario_id: String,
    matched_rule_ids: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct ControlsFile {
    schema: String,
    observations: Vec<ControlObservationJson>,
}

#[derive(Debug, Deserialize)]
struct ControlObservationJson {
    control_type: String,
    action_hash: String,
    status: String,
    actor_hash: String,
    observed_at: i64,
    evidence_hash: Option<DigestJson>,
}

#[derive(Clone, Debug, Deserialize)]
struct PolicyFile {
    schema: String,
    id: String,
    version: String,
    default_decision: String,
    rules: Vec<PolicyRuleFile>,
}

#[derive(Clone, Debug, Deserialize)]
struct PolicyRuleFile {
    id: String,
    priority: u16,
    decision: String,
    reason_code: String,
    when: ConditionFile,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum ConditionFile {
    Always,
    RuntimeKindEquals { value: String },
    RiskClassAtLeast { value: String },
    RiskClassEquals { value: String },
    ProviderFallbacksAllowed { value: bool },
    ControlPresent { value: String },
    ControlAbsent { value: String },
    PluginTrustAtMost { value: String },
    All { conditions: Vec<ConditionFile> },
    Any { conditions: Vec<ConditionFile> },
    Not { condition: Box<ConditionFile> },
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct ModelWaistJson {
    schema: String,
    identity: ModelIdentityJson,
    invocation: ModelInvocationJson,
    observation: ModelObservationJson,
    runtime: RuntimeJson,
    plugin: PluginJson,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct ModelIdentityJson {
    model_class: String,
    model_ref_hash: DigestJson,
    model_slug: String,
    identity_evidence: IdentityEvidenceJson,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum IdentityEvidenceJson {
    Declared,
    ProviderDeclared {
        provider_model_id_hash: DigestJson,
    },
    LocalFilesHashed {
        weights_hash: DigestJson,
        tokenizer_hash: Option<DigestJson>,
        config_hash: Option<DigestJson>,
    },
    ContainerHashed {
        image_hash: DigestJson,
    },
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct ModelInvocationJson {
    action_hash: DigestJson,
    messages_hash: DigestJson,
    system_prompt_hash: Option<DigestJson>,
    tool_spec_hash: Option<DigestJson>,
    response_schema_hash: Option<DigestJson>,
    parameters_hash: DigestJson,
    requested_output: RequestedOutputJson,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum RequestedOutputJson {
    FreeText,
    JsonSchema { schema_hash: DigestJson },
    ToolCall { tool_spec_hash: DigestJson },
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct ModelObservationJson {
    output_text_hash: Option<DigestJson>,
    structured_output_hash: Option<DigestJson>,
    provider_metadata_hash: Option<DigestJson>,
    finish_reason: String,
    usage: TokenUsageJson,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct TokenUsageJson {
    input_tokens: Option<u32>,
    output_tokens: Option<u32>,
    total_tokens: Option<u32>,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct RuntimeJson {
    runtime_kind: String,
    execution_topology: String,
    replay_strength: String,
    determinism: RuntimeDeterminismJson,
    isolation: RuntimeIsolationJson,
    provider_routing: ProviderRoutingJson,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct RuntimeDeterminismJson {
    deterministic: bool,
    seed_bound: bool,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct RuntimeIsolationJson {
    process_isolated: bool,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct ProviderRoutingJson {
    fallbacks_allowed: bool,
    provider_pinned: bool,
    data_collection_policy: String,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct PluginJson {
    plugin_id_hash: DigestJson,
    plugin_version_hash: DigestJson,
    plugin_api_version: String,
    maintainer_class: String,
    normalization: NormalizationJson,
    plugin_manifest_hash: DigestJson,
    plugin_id_hint: String,
    trust_level: String,
}

#[derive(Debug, Deserialize, Serialize, Clone)]
struct NormalizationJson {
    input_normalized: bool,
    output_normalized: bool,
    raw_request_preserved: bool,
    raw_response_preserved: bool,
    secrets_redacted: bool,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct ReceiptJson {
    schema: String,
    receipt_id: String,
    receipt_profile: String,
    action_id: String,
    issued_at: i64,
    issuer: IssuerJson,
    manifest_hash: DigestJson,
    policy: PolicyBindingJson,
    runtime: RuntimeJson,
    model: ModelWaistJson,
    facts: PolicyFactsJson,
    decision: String,
    reason_codes: Vec<String>,
    evidence_summary_hash: DigestJson,
    controls_summary_hash: DigestJson,
    signing: SigningJson,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct IssuerJson {
    name: String,
    key_id: String,
    public_key: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct PolicyBindingJson {
    id: String,
    version: String,
    hash: DigestJson,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct PolicyFactsJson {
    risk_class: String,
    requires_human_review: bool,
    binding_effect_present: bool,
    provider_fallbacks_allowed: bool,
    plugin_trust_level: String,
    runtime_kind: String,
    replay_strength: String,
    model_class: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct SigningJson {
    transcript_encoding: String,
    payload_hash: DigestJson,
    algorithm: String,
    key_id: String,
    signature: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct ComparisonJson {
    schema: String,
    comparison_id: String,
    left_receipt_id: String,
    right_receipt_id: String,
    decision_match: bool,
    action_match: bool,
    manifest_match: bool,
    signing: SigningJson,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct TrustRegistryJson {
    schema: String,
    issuers: Vec<TrustedIssuerJson>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct TrustedIssuerJson {
    key_id: String,
    algorithm: String,
    public_key: String,
    issuer_name: String,
    org_name: String,
    status: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct TrustRegistryV2Json {
    schema: String,
    registry_version: String,
    published_at: String,
    #[serde(default)]
    trust_authorities: Vec<TrustAuthorityJson>,
    issuers: Vec<TrustedIssuerV2Json>,
    signing: SigningJson,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct TrustAuthorityJson {
    key_id: String,
    algorithm: String,
    public_key: String,
    state: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct TrustedIssuerV2Json {
    key_id: String,
    algorithm: String,
    public_key: String,
    issuer_name: String,
    org_name: String,
    usage: String,
    state: String,
    valid_from: String,
    valid_until: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct SignerConfigJson {
    schema: String,
    backend: String,
    issuer_name: String,
    key_id: String,
    secret_key_path: String,
    public_key_path: String,
    trust_registry_path: String,
    revocation_list_path: String,
    receipt_encoding: String,
    #[serde(default)]
    signer_base_url: Option<String>,
    #[serde(default)]
    auth_mode: Option<String>,
    #[serde(default)]
    auth_audience: Option<String>,
    #[serde(default)]
    request_timeout_ms: Option<u64>,
    #[serde(default)]
    trust_registry_url: Option<String>,
    #[serde(default)]
    revocations_url: Option<String>,
    #[serde(default)]
    pinned_trust_authority_public_key: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct RevocationListJson {
    schema: String,
    revoked_keys: Vec<RevokedKeyJson>,
    signing: SigningJson,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[allow(dead_code)]
struct RevocationListV2Json {
    schema: String,
    list_version: String,
    published_at: String,
    revoked_keys: Vec<RevokedKeyJson>,
    signing: SigningJson,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct RevokedKeyJson {
    key_id: String,
    reason: String,
    revoked_at: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct LegacyTrustPolicyJson {
    schema: String,
    trusted_keys: Vec<LegacyTrustedKeyJson>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct LegacyTrustedKeyJson {
    key_id: String,
    algorithm: String,
    public_key: String,
    issuer_names: Vec<String>,
    status: String,
}

#[allow(dead_code)]
struct Bundle {
    manifest_path: PathBuf,
    manifest: ManifestJson,
    manifest_hash: Sha256Digest,
    evidence_summary_hash: Sha256Digest,
    action: ActionJson,
    model_json: ModelWaistJson,
    model: ModelWaist<'static>,
    facts: PolicyFacts,
    controls: Vec<ControlObservation>,
    controls_summary_hash: Sha256Digest,
}

struct PolicyBundle {
    file: PolicyFile,
    compiled: CompiledPolicy<'static>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct HostedReceiptIssueRequest {
    pub receipt_id: Option<String>,
    pub action_id: String,
    pub workflow_kind: String,
    pub schema_key: String,
    pub schema_version: String,
    pub body_json: Value,
    pub domain_metadata: Value,
    pub decision: Option<String>,
    pub issued_at: Option<i64>,
    pub policy_id: Option<String>,
    pub policy_version: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct HostedReceiptIssueResponse {
    pub receipt: Value,
    pub manifest: Value,
    pub manifest_hash: DigestJson,
    pub key_id: String,
    pub trust_registry_version: Option<String>,
    pub revocation_version: Option<String>,
    pub signer_request_id: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct RemoteSignRequest {
    key_id: String,
    issuer_name: String,
    algorithm: String,
    transcript_encoding: String,
    payload_hash: DigestJson,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct RemoteSignResponse {
    signature: String,
    #[serde(default)]
    signer_request_id: Option<String>,
    #[serde(default)]
    trust_registry_version: Option<String>,
    #[serde(default)]
    revocation_version: Option<String>,
}

pub fn create_manifest(
    bundle_dir: &Path,
    action_id: &str,
    artifacts_json: &str,
    created_at: Option<&str>,
) -> Result<Value, HostError> {
    let specs: Vec<ManifestArtifactSpec> = serde_json::from_str(artifacts_json)?;
    let mut artifacts = Vec::with_capacity(specs.len());
    for spec in specs {
        let rel = safe_relative_path(&spec.path)?;
        let full = resolve_rooted_path(bundle_dir, rel)?;
        let bytes = fs::read(&full)?;
        artifacts.push(ManifestArtifactJson {
            artifact_type: spec.artifact_type,
            path: spec.path,
            media_type: spec.media_type,
            size_bytes: bytes.len() as u64,
            hash: digest_json(&sha256(&bytes)),
            schema: spec.schema_id.map(|id| SchemaJson {
                id,
                version: "1.0.0".to_string(),
            }),
        });
    }
    let manifest = ManifestJson {
        schema: "ink.manifest.v2".to_string(),
        action_id: action_id.to_string(),
        created_at: created_at
            .map(ToOwned::to_owned)
            .unwrap_or_else(|| now_timestamp().unix_seconds.to_string()),
        artifacts,
    };
    let out_path = bundle_dir.join("ink_manifest.v2.json");
    write_json(&out_path, &manifest)?;
    let manifest_hash = hash_manifest(&manifest)?;
    Ok(json!({
        "action_id": action_id,
        "manifest_path": out_path,
        "manifest_hash": digest_json(&manifest_hash),
        "evidence_hashes": manifest.artifacts.iter().map(|artifact| artifact.hash.digest.clone()).collect::<Vec<_>>(),
    }))
}

pub fn analyze(
    manifest_path: &Path,
    policy_path: &Path,
    controls_json: Option<&str>,
) -> Result<Value, HostError> {
    let bundle = load_bundle(manifest_path, controls_json)?;
    let policy = load_policy(policy_path)?;
    let mut reason_slots = [ReasonCodeSlot { bytes: b"" }; limits::MAX_REASONS];
    let mut evaluation = EvaluationOut {
        decision: Decision::Warn,
        reasons: ReasonWriter {
            buf: &mut reason_slots,
            len: 0,
        },
    };
    evaluate_policy(
        PolicyInput {
            facts: bundle.facts,
            controls: ControlSet::new(&bundle.controls)?,
        },
        policy.compiled,
        &mut evaluation,
    )?;
    Ok(json!({
        "action_id": bundle.manifest.action_id,
        "manifest_path": manifest_path,
        "output_dir": manifest_path.parent().map(|path| path.display().to_string()).unwrap_or_default(),
        "risk_tier": public_risk_class(bundle.facts.risk_class),
        "required_controls": if bundle.facts.requires_human_review { vec!["human_review"] } else { Vec::<&str>::new() },
        "missing_controls": if bundle.facts.requires_human_review && !has_human_review(&bundle.controls) { vec!["human_review"] } else { Vec::<&str>::new() },
        "recommended_decision": public_decision(evaluation.decision),
        "summary": {
            "reason_codes": reason_strings(evaluation.reasons.as_slice()),
            "policy_id": policy.file.id,
            "policy_version": policy.file.version,
            "manifest_hash": digest_json(&bundle.manifest_hash),
        },
        "report": format!(
            "Analysis for {}\nRisk tier: {}\nRecommended decision: {}\nRequired controls: {}\nMissing controls: {}\nManifest: {}",
            bundle.manifest.action_id,
            public_risk_class(bundle.facts.risk_class),
            public_decision(evaluation.decision),
            if bundle.facts.requires_human_review { "human_review" } else { "none" },
            if bundle.facts.requires_human_review && !has_human_review(&bundle.controls) { "human_review" } else { "none" },
            manifest_path.display(),
        )
    }))
}

pub fn gate(
    manifest_path: &Path,
    policy_path: &Path,
    controls_json: Option<&str>,
    output_path: Option<&Path>,
    demo_signer: bool,
) -> Result<Value, HostError> {
    let bundle = load_bundle(manifest_path, controls_json)?;
    let policy = load_policy(policy_path)?;
    if let Some(raw_controls) = controls_json {
        let controls_path = manifest_path
            .parent()
            .unwrap_or_else(|| Path::new("."))
            .join("controls.supplied.json");
        fs::write(controls_path, raw_controls)?;
    }
    let mut reason_slots = [ReasonCodeSlot { bytes: b"" }; limits::MAX_REASONS];
    let mut evaluation = EvaluationOut {
        decision: Decision::Warn,
        reasons: ReasonWriter {
            buf: &mut reason_slots,
            len: 0,
        },
    };
    evaluate_policy(
        PolicyInput {
            facts: bundle.facts,
            controls: ControlSet::new(&bundle.controls)?,
        },
        policy.compiled,
        &mut evaluation,
    )?;
    let issuer = ensure_local_issuer()?;
    if issuer.requires_demo_consent() && !demo_signer {
        return Err(HostError::Trust(
            "gate requires explicit demo signer approval when the configured backend is demo_file"
                .to_string(),
        ));
    }
    ensure_issueable_receipt_encoding(&issuer.receipt_encoding)?;
    let now = now_timestamp();
    let issued_at = TimestampUtc {
        unix_seconds: now.unix_seconds,
        nanos: 0,
    };
    let payload = build_receipt_payload(
        ReceiptInput {
            receipt_id: leak_receipt_id(format!(
                "urn:ink:receipt:{}-{}",
                issued_at.unix_seconds, now.nanos
            ))?,
            action_id: leak_action_id(bundle.manifest.action_id.clone())?,
            issued_at,
            issuer: IssuerClaim {
                name: leak_bounded::<{ limits::MAX_ISSUER_NAME_LEN }>(issuer.issuer_name.clone())?,
                key_id: leak_key_id(issuer.key_id.clone())?,
                public_key: Ed25519PublicKey(issuer.public_key),
            },
            manifest_hash: bundle.manifest_hash,
            policy: PolicyBinding {
                policy_id: leak_bounded::<{ limits::MAX_POLICY_ID_LEN }>(policy.file.id.clone())?,
                policy_version: leak_bounded::<{ limits::MAX_POLICY_VERSION_LEN }>(
                    policy.file.version.clone(),
                )?,
                policy_hash: sha256(&fs::read(policy_path)?),
            },
            model: bundle.model,
            facts: bundle.facts,
            evidence_summary_hash: bundle.evidence_summary_hash,
            controls_summary_hash: bundle.controls_summary_hash,
        },
        &evaluation,
    )?;
    let receipt = ReceiptJson {
        schema: "ink.receipt.v2".to_string(),
        receipt_id: payload.receipt_id.as_str()?.to_string(),
        receipt_profile: RECEIPT_PROFILE.to_string(),
        action_id: payload.action_id.as_str()?.to_string(),
        issued_at: payload.issued_at.unix_seconds,
        issuer: IssuerJson {
            name: payload.issuer.name.as_str()?.to_string(),
            key_id: payload.issuer.key_id.as_str()?.to_string(),
            public_key: Base64UrlUnpadded::encode_string(&payload.issuer.public_key.0),
        },
        manifest_hash: digest_json(&payload.manifest_hash),
        policy: PolicyBindingJson {
            id: payload.policy.policy_id.as_str()?.to_string(),
            version: payload.policy.policy_version.as_str()?.to_string(),
            hash: digest_json(&payload.policy.policy_hash),
        },
        runtime: bundle.model_json.runtime.clone(),
        model: bundle.model_json.clone(),
        facts: facts_json(bundle.facts),
        decision: public_decision(payload.decision).to_string(),
        reason_codes: reason_strings(payload.reasons),
        evidence_summary_hash: digest_json(&payload.evidence_summary_hash),
        controls_summary_hash: digest_json(&payload.controls_summary_hash),
        signing: SigningJson {
            transcript_encoding: issuer.receipt_encoding.clone(),
            payload_hash: DigestJson {
                algorithm: "sha-256".to_string(),
                digest: String::new(),
            },
            algorithm: "Ed25519".to_string(),
            key_id: payload.issuer.key_id.as_str()?.to_string(),
            signature: String::new(),
        },
    };
    let digest = receipt_digest_for_encoding(&receipt, &payload, &issuer.receipt_encoding)?;
    let sign_result = issuer.sign_digest(&digest)?;
    let signature = Ed25519Signature(sign_result.signature);
    let mut receipt = receipt;
    receipt.signing.payload_hash = digest_json(&digest);
    receipt.signing.signature = Base64UrlUnpadded::encode_string(&signature.0);
    let out_path = output_path.map(PathBuf::from).unwrap_or_else(|| {
        manifest_path
            .parent()
            .unwrap_or_else(|| Path::new("."))
            .join("ink_receipt.v2.json")
    });
    write_json(&out_path, &receipt)?;
    let verification = verify(&out_path, Some(manifest_path))?;
    Ok(json!({
        "action_id": receipt.action_id,
        "receipt_path": out_path,
        "manifest_path": manifest_path,
        "decision": receipt.decision,
        "summary": {
            "receipt_id": receipt.receipt_id,
            "reason_codes": receipt.reason_codes,
            "policy_id": receipt.policy.id,
            "policy_version": receipt.policy.version,
        },
        "signer_request_id": sign_result.signer_request_id,
        "trust_registry_version": sign_result.trust_registry_version,
        "revocation_version": sign_result.revocation_version,
        "verification": verification["verification"].clone(),
        "report": format!(
            "Gate decision for {}: {}\nReason codes: {}\nReceipt ID: {}\nManifest: {}\nReceipt: {}",
            receipt.action_id,
            receipt.decision,
            receipt.reason_codes.join(", "),
            receipt.receipt_id,
            manifest_path.display(),
            out_path.display(),
        )
    }))
}

pub fn issue_hosted_receipt(
    request: &HostedReceiptIssueRequest,
) -> Result<HostedReceiptIssueResponse, HostError> {
    let issuer = ensure_local_issuer()?;
    if issuer.requires_demo_consent() {
        return Err(HostError::Trust(
            "hosted issuance requires a non-demo signer backend".to_string(),
        ));
    }
    ensure_issueable_receipt_encoding(&issuer.receipt_encoding)?;

    let issued_at_seconds = request
        .issued_at
        .unwrap_or_else(|| now_timestamp().unix_seconds);
    let issued_at = TimestampUtc::new(issued_at_seconds, 0)?;
    let issued_at_iso = Utc
        .timestamp_opt(issued_at_seconds, 0)
        .single()
        .unwrap_or_else(Utc::now)
        .to_rfc3339_opts(SecondsFormat::Secs, true);

    let body_json = request.body_json.clone();
    let domain_metadata = request.domain_metadata.clone();
    let body_bytes = canonicalize_legacy(&body_json);
    let metadata_bytes = canonicalize_legacy(&domain_metadata);
    let policy_id = request
        .policy_id
        .clone()
        .unwrap_or_else(|| "HOSTED_WORKFLOW_POLICY".to_string());
    let policy_version = request
        .policy_version
        .clone()
        .unwrap_or_else(|| "1.0.0".to_string());
    let manifest = ManifestJson {
        schema: "ink.manifest.v2".to_string(),
        action_id: request.action_id.clone(),
        created_at: issued_at_iso,
        artifacts: vec![
            ManifestArtifactJson {
                artifact_type: "workflow_body_json".to_string(),
                path: "workflow-body.json".to_string(),
                media_type: "application/json".to_string(),
                size_bytes: body_bytes.len() as u64,
                hash: digest_json(&sha256(&body_bytes)),
                schema: Some(SchemaJson {
                    id: request.schema_key.clone(),
                    version: request.schema_version.clone(),
                }),
            },
            ManifestArtifactJson {
                artifact_type: "domain_metadata_json".to_string(),
                path: "domain-metadata.json".to_string(),
                media_type: "application/json".to_string(),
                size_bytes: metadata_bytes.len() as u64,
                hash: digest_json(&sha256(&metadata_bytes)),
                schema: None,
            },
        ],
    };
    let manifest_hash = hash_manifest(&manifest)?;
    let evidence_summary_hash = hash_evidence_summary(&manifest)?;
    let controls_summary_hash = hash_controls_summary(&[]);
    let receipt_id = request.receipt_id.clone().unwrap_or_else(|| {
        format!(
            "urn:ink:receipt:hosted:{}:{}",
            issued_at_seconds,
            hex::encode(&sha256(&body_bytes).0[..6])
        )
    });
    let model_json = hosted_model_json(request, &body_bytes, &metadata_bytes);
    let model = normalize_model(&model_json)?;
    let risk_class = domain_metadata
        .get("risk_class")
        .and_then(Value::as_str)
        .unwrap_or("medium");
    let facts = PolicyFacts {
        risk_class: risk_class_from_str(risk_class)?,
        requires_human_review: domain_metadata
            .get("requires_human_review")
            .and_then(Value::as_bool)
            .unwrap_or(false),
        binding_effect_present: false,
        provider_fallbacks_allowed: false,
        plugin_trust_level: PluginTrustFact::FirstPartyReference,
        runtime_kind: RuntimeKind::HostedModelGateway,
        replay_strength: ReplayStrength::DeclaredOnly,
        model_class: ModelClass::HostedApi,
    };
    let mut reason_slots = [ReasonCodeSlot { bytes: b"" }; limits::MAX_REASONS];
    reason_slots[0] = ReasonCodeSlot {
        bytes: b"HOSTED_WORKFLOW_ISSUED",
    };
    let decision = policy_decision_from_str(request.decision.as_deref().unwrap_or("warn"))?;
    let evaluation = EvaluationOut {
        decision,
        reasons: ReasonWriter {
            buf: &mut reason_slots,
            len: 1,
        },
    };
    let payload = build_receipt_payload(
        ReceiptInput {
            receipt_id: leak_receipt_id(receipt_id)?,
            action_id: leak_action_id(request.action_id.clone())?,
            issued_at,
            issuer: IssuerClaim {
                name: leak_bounded::<{ limits::MAX_ISSUER_NAME_LEN }>(issuer.issuer_name.clone())?,
                key_id: leak_key_id(issuer.key_id.clone())?,
                public_key: Ed25519PublicKey(issuer.public_key),
            },
            manifest_hash,
            policy: PolicyBinding {
                policy_id: leak_bounded::<{ limits::MAX_POLICY_ID_LEN }>(policy_id.clone())?,
                policy_version: leak_bounded::<{ limits::MAX_POLICY_VERSION_LEN }>(
                    policy_version.clone(),
                )?,
                policy_hash: sha256(
                    format!(
                        "{}:{}:{}:{}",
                        policy_id, policy_version, request.workflow_kind, request.schema_key
                    )
                    .as_bytes(),
                ),
            },
            model,
            facts,
            evidence_summary_hash,
            controls_summary_hash,
        },
        &evaluation,
    )?;
    let mut receipt = ReceiptJson {
        schema: "ink.receipt.v2".to_string(),
        receipt_id: payload.receipt_id.as_str()?.to_string(),
        receipt_profile: RECEIPT_PROFILE.to_string(),
        action_id: payload.action_id.as_str()?.to_string(),
        issued_at: payload.issued_at.unix_seconds,
        issuer: IssuerJson {
            name: payload.issuer.name.as_str()?.to_string(),
            key_id: payload.issuer.key_id.as_str()?.to_string(),
            public_key: Base64UrlUnpadded::encode_string(&payload.issuer.public_key.0),
        },
        manifest_hash: digest_json(&payload.manifest_hash),
        policy: PolicyBindingJson {
            id: payload.policy.policy_id.as_str()?.to_string(),
            version: payload.policy.policy_version.as_str()?.to_string(),
            hash: digest_json(&payload.policy.policy_hash),
        },
        runtime: model_json.runtime.clone(),
        model: model_json.clone(),
        facts: facts_json(facts),
        decision: public_decision(payload.decision).to_string(),
        reason_codes: reason_strings(payload.reasons),
        evidence_summary_hash: digest_json(&payload.evidence_summary_hash),
        controls_summary_hash: digest_json(&payload.controls_summary_hash),
        signing: SigningJson {
            transcript_encoding: issuer.receipt_encoding.clone(),
            payload_hash: DigestJson {
                algorithm: "sha-256".to_string(),
                digest: String::new(),
            },
            algorithm: "Ed25519".to_string(),
            key_id: payload.issuer.key_id.as_str()?.to_string(),
            signature: String::new(),
        },
    };
    let digest = receipt_digest_for_encoding(&receipt, &payload, &issuer.receipt_encoding)?;
    let sign_result = issuer.sign_digest(&digest)?;
    receipt.signing.payload_hash = digest_json(&digest);
    receipt.signing.signature = Base64UrlUnpadded::encode_string(&sign_result.signature);

    Ok(HostedReceiptIssueResponse {
        receipt: serde_json::to_value(&receipt)?,
        manifest: serde_json::to_value(&manifest)?,
        manifest_hash: digest_json(&manifest_hash),
        key_id: receipt.signing.key_id,
        trust_registry_version: sign_result.trust_registry_version,
        revocation_version: sign_result.revocation_version,
        signer_request_id: sign_result.signer_request_id,
    })
}

pub fn verify(receipt_path: &Path, manifest_path: Option<&Path>) -> Result<Value, HostError> {
    let raw = fs::read_to_string(receipt_path)?;
    let value: Value = serde_json::from_str(&raw)?;
    if value.get("schema").and_then(Value::as_str) == Some("ink.receipt.v1") {
        return verify_legacy_v1(receipt_path, &value);
    }
    let receipt: ReceiptJson = serde_json::from_str(&raw)?;
    let sibling = sibling_manifest(receipt_path);
    let manifest_candidate = manifest_path.map(PathBuf::from).or(sibling);
    let controls_candidate = manifest_candidate
        .as_ref()
        .and_then(|path| sibling_controls(path));
    let manifest_bytes = manifest_candidate
        .as_ref()
        .map(fs::read)
        .transpose()
        .map_err(HostError::from)?;
    let controls_bytes = controls_candidate
        .as_ref()
        .map(fs::read)
        .transpose()
        .map_err(HostError::from)?;
    let root = config_root()?;
    let signer = load_signer_config().ok();
    let trust_path = signer
        .as_ref()
        .map(|config| resolve_config_path(&root, &config.trust_registry_path))
        .unwrap_or_else(|| root.join(TRUST_REGISTRY_FILE));
    let revocation_path = signer
        .as_ref()
        .map(|config| resolve_config_path(&root, &config.revocation_list_path))
        .unwrap_or_else(|| root.join(REVOCATION_LIST_FILE));
    let trust_registry_bytes = trust_path
        .exists()
        .then(|| fs::read(&trust_path))
        .transpose()?;
    let revocation_list_bytes = revocation_path
        .exists()
        .then(|| fs::read(&revocation_path))
        .transpose()?;
    let compatibility_policy =
        serde_json::to_vec(&ink_receipt_v2::VerifyPolicyJson::host_compatibility())?;
    let report = ink_receipt_v2::verify_receipt(
        raw.as_bytes(),
        manifest_bytes.as_deref(),
        controls_bytes.as_deref(),
        trust_registry_bytes.as_deref(),
        revocation_list_bytes.as_deref(),
        Some(compatibility_policy.as_slice()),
        None,
    )
    .map_err(|err| match err {
        ink_receipt_v2::ReceiptV2Error::Json(inner) => HostError::Json(inner),
        ink_receipt_v2::ReceiptV2Error::Core(inner) => HostError::Core(inner),
        ink_receipt_v2::ReceiptV2Error::InvalidInput(message) => HostError::InvalidInput(message),
        ink_receipt_v2::ReceiptV2Error::Trust(message) => HostError::Trust(message),
    })?;
    match report.code.as_str() {
        "REVOKED_ISSUER_KEY" => {
            return Err(HostError::Trust(format!(
                "trusted key {} is revoked",
                receipt.signing.key_id
            )))
        }
        "UNTRUSTED_ISSUER" => {
            return Err(HostError::Trust(format!(
                "unknown trusted key {}",
                receipt.signing.key_id
            )))
        }
        "UNTRUSTED_REVOCATION_LIST_SIGNER"
        | "REVOCATION_LIST_PAYLOAD_HASH_MISMATCH"
        | "REVOCATION_LIST_UNSUPPORTED_SIGNATURE_ALGORITHM"
        | "REVOCATION_LIST_INVALID_SIGNATURE" => return Err(HostError::Trust(report.code.clone())),
        _ => {}
    }
    let checks = report
        .checks
        .iter()
        .map(|check| {
            json!({
                "id": check.id,
                "status": check.status,
                "reason_code": check.reason_code,
            })
        })
        .collect::<Vec<_>>();
    Ok(json!({
        "action_id": receipt.action_id,
        "receipt_path": receipt_path,
        "manifest_path": manifest_candidate,
        "decision": receipt.decision,
        "summary": {
            "receipt_id": receipt.receipt_id,
            "reason_codes": receipt.reason_codes,
        },
        "verification": {
            "receipt_version": "v2",
            "scope": report.scope,
            "overall": if report.status == "valid" { "pass" } else { "fail" },
            "issuer_key_id": receipt.issuer.key_id,
            "checks": checks,
        },
        "report": format!(
            "Verification for {}\nReceipt ID: {}\nDecision: {}\nVerification scope: {}\nOverall: {}",
            receipt_path.display(),
            receipt.receipt_id,
            receipt.decision,
            report.scope,
            if report.status == "valid" { "pass" } else { "fail" },
        )
    }))
}

pub fn compare(
    left_receipt: &Path,
    right_receipt: &Path,
    output_path: Option<&Path>,
) -> Result<Value, HostError> {
    let left_verify = verify(left_receipt, sibling_manifest(left_receipt).as_deref())?;
    let right_verify = verify(right_receipt, sibling_manifest(right_receipt).as_deref())?;
    if left_verify["verification"]["overall"] != "pass"
        || right_verify["verification"]["overall"] != "pass"
    {
        return Err(HostError::Trust(
            "compare requires two fully valid v2 receipts".to_string(),
        ));
    }
    let left: ReceiptJson = serde_json::from_str(&fs::read_to_string(left_receipt)?)?;
    let right: ReceiptJson = serde_json::from_str(&fs::read_to_string(right_receipt)?)?;
    let left_payload = receipt_payload_from_json(&left)?;
    let right_payload = receipt_payload_from_json(&right)?;
    let mut out = ComparisonOut {
        comparable: false,
        decision_match: false,
        action_match: false,
        manifest_match: false,
    };
    compare_receipts(
        VerifiedReceiptSummary::from_payload(&left_payload)?,
        VerifiedReceiptSummary::from_payload(&right_payload)?,
        &mut out,
    )?;
    let packet = ComparisonJson {
        schema: "receipt.comparison.v2".to_string(),
        comparison_id: {
            let now = now_timestamp();
            format!("urn:ink:comparison:{}-{}", now.unix_seconds, now.nanos)
        },
        left_receipt_id: left.receipt_id.clone(),
        right_receipt_id: right.receipt_id.clone(),
        decision_match: out.decision_match,
        action_match: out.action_match,
        manifest_match: out.manifest_match,
        signing: sign_comparison_packet(&left, &right, &out)?,
    };
    let out_path = output_path.map(PathBuf::from).unwrap_or_else(|| {
        left_receipt
            .parent()
            .unwrap_or_else(|| Path::new("."))
            .join("receipt_comparison.v2.json")
    });
    write_json(&out_path, &packet)?;
    Ok(json!({
        "comparison_path": out_path,
        "output_dir": out_path.parent().map(|path| path.display().to_string()).unwrap_or_default(),
        "left_receipt_path": left_receipt,
        "right_receipt_path": right_receipt,
        "summary": {
            "left_receipt_id": packet.left_receipt_id,
            "right_receipt_id": packet.right_receipt_id,
            "decision_match": packet.decision_match,
            "action_match": packet.action_match,
            "manifest_match": packet.manifest_match,
        },
        "report": format!(
            "BLKBX Lab Comparison Summary\nLeft receipt: {}\nRight receipt: {}\nDecision match: {}\nAction match: {}\nComparison packet: {}",
            packet.left_receipt_id,
            packet.right_receipt_id,
            packet.decision_match,
            packet.action_match,
            out_path.display(),
        )
    }))
}

pub fn doctor(initialize_local_issuer: bool) -> Result<Value, HostError> {
    let mut notes = Vec::new();
    let mut checks = vec![
        json!({"name": "native_core", "status": "ok"}),
        json!({"name": "receipt_v2", "status": "ok"}),
    ];
    let mut demo_ready = false;
    let mut real_replay_ready = false;
    if initialize_local_issuer {
        let issuer = ensure_local_issuer()?;
        notes.push(format!("initialized signer {}", issuer.key_id));
        checks.push(json!({"name": "local_issuer", "status": "ok"}));
        checks.push(json!({"name": "signer_backend", "status": issuer.backend}));
        checks.push(receipt_encoding_check(&issuer.receipt_encoding));
        checks.push(json!({"name": "trust_registry", "status": "ok"}));
        checks.push(json!({"name": "revocation_list", "status": "ok"}));
        if let Some(note) = receipt_encoding_note(&issuer.receipt_encoding) {
            notes.push(note);
        }
        demo_ready = issuer.requires_demo_consent()
            && receipt_encoding_allows_issuance(&issuer.receipt_encoding);
        real_replay_ready = matches!(issuer.backend.as_str(), "file_ed25519" | "remote_kms_v1")
            && receipt_encoding_allows_issuance(&issuer.receipt_encoding);
    } else if let Ok(config) = load_signer_config() {
        let trust_registry_exists = if config.backend == "remote_kms_v1" {
            config.trust_registry_url.is_some()
        } else {
            config_root()?.join(&config.trust_registry_path).exists()
        };
        let revocation_list_exists = if config.backend == "remote_kms_v1" {
            config.revocations_url.is_some()
        } else {
            config_root()?.join(&config.revocation_list_path).exists()
        };
        checks.push(json!({"name": "local_issuer", "status": "ok"}));
        checks.push(json!({"name": "signer_backend", "status": config.backend}));
        checks.push(receipt_encoding_check(&config.receipt_encoding));
        checks.push(json!({"name": "trust_registry", "status": if trust_registry_exists { "ok" } else { "missing" }}));
        checks.push(json!({"name": "revocation_list", "status": if revocation_list_exists { "ok" } else { "missing" }}));
        if let Some(note) = receipt_encoding_note(&config.receipt_encoding) {
            notes.push(note);
        }
        demo_ready = config.backend == "demo_file"
            && receipt_encoding_allows_issuance(&config.receipt_encoding);
        real_replay_ready = matches!(config.backend.as_str(), "file_ed25519" | "remote_kms_v1")
            && trust_registry_exists
            && revocation_list_exists
            && receipt_encoding_allows_issuance(&config.receipt_encoding);
    } else {
        checks.push(json!({"name": "local_issuer", "status": "missing"}));
        notes.push(
            "run doctor with initialize_local_issuer=true to bootstrap the local signer"
                .to_string(),
        );
    }
    notes.push("demo_file requires explicit --demo-signer; file_ed25519 and remote_kms_v1 can issue receipts without demo consent once configured".to_string());
    Ok(json!({
        "status": "ready",
        "checks": checks,
        "notes": notes,
        "demo_ready": demo_ready,
        "real_replay_ready": real_replay_ready,
    }))
}

fn load_bundle(manifest_path: &Path, controls_json: Option<&str>) -> Result<Bundle, HostError> {
    let manifest: ManifestJson = serde_json::from_str(&fs::read_to_string(manifest_path)?)?;
    if manifest.schema != "ink.manifest.v2" {
        return Err(HostError::InvalidInput(
            "expected ink.manifest.v2".to_string(),
        ));
    }
    let root = manifest_path
        .parent()
        .ok_or_else(|| HostError::UnsafePath(manifest_path.display().to_string()))?;
    let mut action: Option<ActionJson> = None;
    let mut model_json: Option<ModelWaistJson> = None;
    let mut prompt_hash: Option<DigestJson> = None;
    for artifact in &manifest.artifacts {
        let rel = safe_relative_path(&artifact.path)?;
        let full = resolve_rooted_path(root, rel)?;
        let bytes = fs::read(full)?;
        let digest = sha256(&bytes);
        if digest_json(&digest).digest != artifact.hash.digest {
            return Err(HostError::InvalidInput(format!(
                "artifact hash mismatch: {}",
                artifact.path
            )));
        }
        match artifact.artifact_type.as_str() {
            "prompt_text" => prompt_hash = Some(digest_json(&digest)),
            "action_json" => action = Some(serde_json::from_slice(&bytes)?),
            "model_waist_json" => model_json = Some(serde_json::from_slice(&bytes)?),
            _ => {}
        }
    }
    let action = action
        .ok_or_else(|| HostError::InvalidInput("missing action_json artifact".to_string()))?;
    if action.schema != "ink.action.v1" {
        return Err(HostError::InvalidInput(
            "expected ink.action.v1".to_string(),
        ));
    }
    if prompt_hash.as_ref().map(|digest| &digest.digest) != Some(&action.prompt_hash.digest) {
        return Err(HostError::InvalidInput(
            "prompt/action binding mismatch".to_string(),
        ));
    }
    let model_json = model_json
        .ok_or_else(|| HostError::InvalidInput("missing model_waist_json artifact".to_string()))?;
    let model = normalize_model(&model_json)?;
    let controls = if let Some(raw) = controls_json {
        normalize_controls(raw)?
    } else {
        let sibling = manifest_path
            .parent()
            .unwrap_or_else(|| Path::new("."))
            .join("controls.supplied.json");
        if sibling.exists() {
            normalize_controls(&fs::read_to_string(sibling)?)?
        } else {
            Vec::new()
        }
    };
    let facts = PolicyFacts {
        risk_class: risk_class_from_str(&action.risk_class)?,
        requires_human_review: risk_class_from_str(&action.risk_class)? == RiskClass::High,
        binding_effect_present: action.operation == "approve_claim",
        provider_fallbacks_allowed: model.runtime.provider_routing.fallbacks_allowed,
        plugin_trust_level: plugin_trust_fact(model.plugin.trust_level),
        runtime_kind: model.runtime.runtime_kind,
        replay_strength: model.runtime.replay_strength,
        model_class: model.identity.model_class,
    };
    Ok(Bundle {
        manifest_path: manifest_path.to_path_buf(),
        manifest_hash: hash_manifest(&manifest)?,
        evidence_summary_hash: hash_evidence_summary(&manifest)?,
        controls_summary_hash: hash_controls_summary(&controls),
        action,
        model_json,
        model,
        facts,
        controls,
        manifest,
    })
}

fn load_policy(policy_path: &Path) -> Result<PolicyBundle, HostError> {
    let raw = fs::read(policy_path)?;
    let file: PolicyFile = serde_json::from_slice(&raw)?;
    if file.schema != "ink.policy.v1" {
        return Err(HostError::InvalidInput(
            "expected ink.policy.v1".to_string(),
        ));
    }
    let mut rules_json = file.rules.clone();
    rules_json.sort_by_key(|rule| std::cmp::Reverse(rule.priority));
    let mut nodes = Vec::new();
    let mut rules = Vec::new();
    for rule in &rules_json {
        let root = compile_condition(&rule.when, &mut nodes)?;
        rules.push(CompiledRule {
            rule_id_hash: sha256(rule.id.as_bytes()),
            priority: rule.priority,
            root,
            effect: RuleEffect {
                decision: policy_decision_from_str(&rule.decision)?,
                reason: leak_reason(rule.reason_code.clone())?,
            },
        });
    }
    let compiled = CompiledPolicy {
        policy_id: leak_bounded::<{ limits::MAX_POLICY_ID_LEN }>(file.id.clone())?,
        policy_version: leak_bounded::<{ limits::MAX_POLICY_VERSION_LEN }>(file.version.clone())?,
        policy_hash: sha256(&raw),
        nodes: Box::leak(nodes.into_boxed_slice()),
        rules: Box::leak(rules.into_boxed_slice()),
        default_effect: RuleEffect {
            decision: policy_decision_from_str(&file.default_decision)?,
            reason: leak_reason("POLICY_DEFAULT_FAIL".to_string())?,
        },
    };
    Ok(PolicyBundle { file, compiled })
}

fn compile_condition(
    condition: &ConditionFile,
    nodes: &mut Vec<ConditionNode>,
) -> Result<u16, HostError> {
    match condition {
        ConditionFile::Always => push_node(
            nodes,
            ConditionNode {
                op: ConditionOp::Always,
                left: 0,
                right: 0,
                value: ConditionValue::None,
            },
        ),
        ConditionFile::RuntimeKindEquals { value } => push_node(
            nodes,
            ConditionNode {
                op: ConditionOp::RuntimeKindEquals,
                left: 0,
                right: 0,
                value: ConditionValue::RuntimeKind(runtime_kind_from_str(value)?),
            },
        ),
        ConditionFile::RiskClassEquals { value } => push_node(
            nodes,
            ConditionNode {
                op: ConditionOp::RiskClassEquals,
                left: 0,
                right: 0,
                value: ConditionValue::RiskClass(risk_class_from_str(value)?),
            },
        ),
        ConditionFile::RiskClassAtLeast { value } => push_node(
            nodes,
            ConditionNode {
                op: ConditionOp::RiskClassAtLeast,
                left: 0,
                right: 0,
                value: ConditionValue::RiskClass(risk_class_from_str(value)?),
            },
        ),
        ConditionFile::ProviderFallbacksAllowed { value } => push_node(
            nodes,
            ConditionNode {
                op: ConditionOp::ProviderFallbacksAllowed,
                left: 0,
                right: 0,
                value: ConditionValue::Bool(*value),
            },
        ),
        ConditionFile::ControlPresent { value } => push_node(
            nodes,
            ConditionNode {
                op: ConditionOp::ControlApproved,
                left: 0,
                right: 0,
                value: ConditionValue::ControlType(control_type_from_str(value)?),
            },
        ),
        ConditionFile::ControlAbsent { value } => {
            let inner = push_node(
                nodes,
                ConditionNode {
                    op: ConditionOp::ControlApproved,
                    left: 0,
                    right: 0,
                    value: ConditionValue::ControlType(control_type_from_str(value)?),
                },
            )?;
            push_node(
                nodes,
                ConditionNode {
                    op: ConditionOp::Not,
                    left: inner,
                    right: 0,
                    value: ConditionValue::None,
                },
            )
        }
        ConditionFile::PluginTrustAtMost { value } => push_node(
            nodes,
            ConditionNode {
                op: ConditionOp::PluginTrustLevelAtMost,
                left: 0,
                right: 0,
                value: ConditionValue::PluginTrust(plugin_trust_fact_from_str(value)?),
            },
        ),
        ConditionFile::All { conditions } => chain_conditions(nodes, conditions, true),
        ConditionFile::Any { conditions } => chain_conditions(nodes, conditions, false),
        ConditionFile::Not { condition } => {
            let inner = compile_condition(condition, nodes)?;
            push_node(
                nodes,
                ConditionNode {
                    op: ConditionOp::Not,
                    left: inner,
                    right: 0,
                    value: ConditionValue::None,
                },
            )
        }
    }
}

fn chain_conditions(
    nodes: &mut Vec<ConditionNode>,
    conditions: &[ConditionFile],
    all: bool,
) -> Result<u16, HostError> {
    let mut iter = conditions.iter();
    let first = iter
        .next()
        .ok_or_else(|| HostError::InvalidInput("empty condition list".to_string()))?;
    let mut current = compile_condition(first, nodes)?;
    for condition in iter {
        let next = compile_condition(condition, nodes)?;
        current = push_node(
            nodes,
            ConditionNode {
                op: if all {
                    ConditionOp::And
                } else {
                    ConditionOp::Or
                },
                left: current,
                right: next,
                value: ConditionValue::None,
            },
        )?;
    }
    Ok(current)
}

fn push_node(nodes: &mut Vec<ConditionNode>, node: ConditionNode) -> Result<u16, HostError> {
    let index = nodes.len();
    if index >= limits::MAX_CONDITION_NODES {
        return Err(HostError::InvalidInput(
            "too many condition nodes".to_string(),
        ));
    }
    nodes.push(node);
    Ok(index as u16)
}

fn normalize_model(json_model: &ModelWaistJson) -> Result<ModelWaist<'static>, HostError> {
    if json_model.schema != "ink.model-waist.v1" {
        return Err(HostError::InvalidInput(
            "expected ink.model-waist.v1".to_string(),
        ));
    }
    let model = ModelWaist {
        identity: ModelIdentityClaim {
            model_class: model_class_from_str(&json_model.identity.model_class)?,
            model_ref_hash: parse_digest(&json_model.identity.model_ref_hash)?,
            model_slug: leak_bounded::<{ limits::MAX_MODEL_SLUG_LEN }>(
                json_model.identity.model_slug.clone(),
            )?,
            identity_evidence: match &json_model.identity.identity_evidence {
                IdentityEvidenceJson::Declared => IdentityEvidence::Declared,
                IdentityEvidenceJson::ProviderDeclared {
                    provider_model_id_hash,
                } => IdentityEvidence::ProviderDeclared {
                    provider_model_id_hash: parse_digest(provider_model_id_hash)?,
                },
                IdentityEvidenceJson::LocalFilesHashed {
                    weights_hash,
                    tokenizer_hash,
                    config_hash,
                } => IdentityEvidence::LocalFilesHashed {
                    weights_hash: parse_digest(weights_hash)?,
                    tokenizer_hash: tokenizer_hash.as_ref().map(parse_digest).transpose()?,
                    config_hash: config_hash.as_ref().map(parse_digest).transpose()?,
                },
                IdentityEvidenceJson::ContainerHashed { image_hash } => {
                    IdentityEvidence::ContainerHashed {
                        image_hash: parse_digest(image_hash)?,
                    }
                }
            },
        },
        invocation: ModelInvocationClaim {
            action_hash: parse_digest(&json_model.invocation.action_hash)?,
            messages_hash: parse_digest(&json_model.invocation.messages_hash)?,
            system_prompt_hash: json_model
                .invocation
                .system_prompt_hash
                .as_ref()
                .map(parse_digest)
                .transpose()?,
            tool_spec_hash: json_model
                .invocation
                .tool_spec_hash
                .as_ref()
                .map(parse_digest)
                .transpose()?,
            response_schema_hash: json_model
                .invocation
                .response_schema_hash
                .as_ref()
                .map(parse_digest)
                .transpose()?,
            parameters_hash: parse_digest(&json_model.invocation.parameters_hash)?,
            requested_output: match &json_model.invocation.requested_output {
                RequestedOutputJson::FreeText => RequestedOutput::FreeText,
                RequestedOutputJson::JsonSchema { schema_hash } => RequestedOutput::JsonSchema {
                    schema_hash: parse_digest(schema_hash)?,
                },
                RequestedOutputJson::ToolCall { tool_spec_hash } => RequestedOutput::ToolCall {
                    tool_spec_hash: parse_digest(tool_spec_hash)?,
                },
            },
        },
        observation: ModelObservationClaim {
            output_text_hash: json_model
                .observation
                .output_text_hash
                .as_ref()
                .map(parse_digest)
                .transpose()?,
            structured_output_hash: json_model
                .observation
                .structured_output_hash
                .as_ref()
                .map(parse_digest)
                .transpose()?,
            provider_metadata_hash: json_model
                .observation
                .provider_metadata_hash
                .as_ref()
                .map(parse_digest)
                .transpose()?,
            finish_reason: finish_reason_from_str(&json_model.observation.finish_reason),
            usage: TokenUsage {
                input_tokens: json_model.observation.usage.input_tokens,
                output_tokens: json_model.observation.usage.output_tokens,
                total_tokens: json_model.observation.usage.total_tokens,
            },
        },
        runtime: RuntimeClaim {
            runtime_kind: runtime_kind_from_str(&json_model.runtime.runtime_kind)?,
            execution_topology: execution_topology_from_str(
                &json_model.runtime.execution_topology,
            )?,
            replay_strength: replay_strength_from_str(&json_model.runtime.replay_strength)?,
            determinism: DeterminismClaim {
                deterministic: json_model.runtime.determinism.deterministic,
                seed_bound: json_model.runtime.determinism.seed_bound,
            },
            isolation: IsolationClaim {
                process_isolated: json_model.runtime.isolation.process_isolated,
            },
            provider_routing: ProviderRoutingClaim {
                fallbacks_allowed: json_model.runtime.provider_routing.fallbacks_allowed,
                provider_pinned: json_model.runtime.provider_routing.provider_pinned,
                data_collection_policy: data_collection_from_str(
                    &json_model.runtime.provider_routing.data_collection_policy,
                ),
            },
        },
        plugin: PluginClaim {
            plugin_id_hash: parse_digest(&json_model.plugin.plugin_id_hash)?,
            plugin_version_hash: parse_digest(&json_model.plugin.plugin_version_hash)?,
            plugin_api_version: PluginApiVersion::V1,
            maintainer_class: maintainer_class_from_str(&json_model.plugin.maintainer_class),
            normalization: NormalizationClaim {
                input_normalized: json_model.plugin.normalization.input_normalized,
                output_normalized: json_model.plugin.normalization.output_normalized,
                raw_request_preserved: json_model.plugin.normalization.raw_request_preserved,
                raw_response_preserved: json_model.plugin.normalization.raw_response_preserved,
                secrets_redacted: json_model.plugin.normalization.secrets_redacted,
            },
            plugin_manifest_hash: parse_digest(&json_model.plugin.plugin_manifest_hash)?,
            plugin_id_hint: leak_bounded::<{ limits::MAX_PLUGIN_ID_HINT_LEN }>(
                json_model.plugin.plugin_id_hint.clone(),
            )?,
            trust_level: plugin_trust_from_str(&json_model.plugin.trust_level),
        },
    };
    model.validate()?;
    Ok(model)
}

fn normalize_controls(raw: &str) -> Result<Vec<ControlObservation>, HostError> {
    let controls: ControlsFile = serde_json::from_str(raw)?;
    if controls.schema != "ink.controls.v1" {
        return Err(HostError::InvalidInput(
            "expected ink.controls.v1".to_string(),
        ));
    }
    controls
        .observations
        .into_iter()
        .map(|observation| {
            Ok(ControlObservation {
                control_type: control_type_from_str(&observation.control_type)?,
                action_hash: parse_hex_digest(&observation.action_hash)?,
                status: control_status_from_str(&observation.status)?,
                actor_hash: parse_hex_digest(&observation.actor_hash)?,
                observed_at: TimestampUtc::new(observation.observed_at, 0)?,
                evidence_hash: observation
                    .evidence_hash
                    .as_ref()
                    .map(parse_digest)
                    .transpose()?,
            })
        })
        .collect()
}

fn receipt_payload_from_json(receipt: &ReceiptJson) -> Result<ReceiptPayload<'static>, HostError> {
    let model = normalize_model(&receipt.model)?;
    let facts = PolicyFacts {
        risk_class: risk_class_from_str(&receipt.facts.risk_class)?,
        requires_human_review: receipt.facts.requires_human_review,
        binding_effect_present: receipt.facts.binding_effect_present,
        provider_fallbacks_allowed: receipt.facts.provider_fallbacks_allowed,
        plugin_trust_level: plugin_trust_fact_from_str(&receipt.facts.plugin_trust_level)?,
        runtime_kind: runtime_kind_from_str(&receipt.facts.runtime_kind)?,
        replay_strength: replay_strength_from_str(&receipt.facts.replay_strength)?,
        model_class: model_class_from_str(&receipt.facts.model_class)?,
    };
    let mut slots = Vec::with_capacity(receipt.reason_codes.len());
    for reason in &receipt.reason_codes {
        slots.push(ReasonCodeSlot {
            bytes: Box::leak(reason.clone().into_boxed_str()).as_bytes(),
        });
    }
    let leaked_slots = Box::leak(slots.into_boxed_slice());
    if runtime_kind_from_str(&receipt.runtime.runtime_kind)? != model.runtime.runtime_kind
        || execution_topology_from_str(&receipt.runtime.execution_topology)?
            != model.runtime.execution_topology
        || replay_strength_from_str(&receipt.runtime.replay_strength)?
            != model.runtime.replay_strength
    {
        return Err(HostError::InvalidInput(
            "receipt runtime projection does not match model runtime".to_string(),
        ));
    }
    let payload = ReceiptPayload {
        schema_version: ReceiptSchemaVersion::V2,
        receipt_id: leak_receipt_id(receipt.receipt_id.clone())?,
        receipt_profile: ReceiptProfile::ThinWaistV2,
        action_id: leak_action_id(receipt.action_id.clone())?,
        issued_at: TimestampUtc::new(receipt.issued_at, 0)?,
        issuer: IssuerClaim {
            name: leak_bounded::<{ limits::MAX_ISSUER_NAME_LEN }>(receipt.issuer.name.clone())?,
            key_id: leak_key_id(receipt.issuer.key_id.clone())?,
            public_key: Ed25519PublicKey(decode_fixed::<32>(&receipt.issuer.public_key)?),
        },
        manifest_hash: parse_digest(&receipt.manifest_hash)?,
        policy: PolicyBinding {
            policy_id: leak_bounded::<{ limits::MAX_POLICY_ID_LEN }>(receipt.policy.id.clone())?,
            policy_version: leak_bounded::<{ limits::MAX_POLICY_VERSION_LEN }>(
                receipt.policy.version.clone(),
            )?,
            policy_hash: parse_digest(&receipt.policy.hash)?,
        },
        model,
        facts,
        decision: policy_decision_from_public(&receipt.decision),
        reasons: leaked_slots,
        evidence_summary_hash: parse_digest(&receipt.evidence_summary_hash)?,
        controls_summary_hash: parse_digest(&receipt.controls_summary_hash)?,
    };
    payload.validate()?;
    Ok(payload)
}

// Current ink.receipt.v2 artifacts stay host-level, but the host should still be
// able to project them into the neutral kernel envelope and exercise the new
// canonical hashing and lifecycle rules.
#[allow(dead_code)]
fn project_v2_receipt_to_kernel(
    receipt: &ReceiptJson,
    payload: &ReceiptPayload<'_>,
) -> Result<ReceiptEnvelope, HostError> {
    let schema_id = SchemaId::from_str("ink.receipt.v2")?;
    let schema_authority = SchemaAuthority::from_str("ink-host")?;
    let domain_tag = DomainTag::from_str("compat-v2")?;
    let issuer_id = kernel_projection_issuer_id(&receipt.issuer.key_id)?;
    let sequence = u64::try_from(receipt.issued_at).map_err(|_| {
        HostError::InvalidInput("receipt issued_at must be non-negative".to_string())
    })?;
    let claim_hash = kernel_projection_claim_hash(receipt, payload)?;
    let trace_hash = to_kernel_digest(receipt_transcript_hash(payload)?);

    let projected = ReceiptEnvelope::create(
        schema_id,
        to_kernel_digest(sha256(b"ink.receipt.v2")),
        schema_authority,
        domain_tag,
        to_kernel_digest(payload.model.invocation.action_hash),
        issuer_id,
        sequence,
        claim_hash,
        to_kernel_digest(payload.evidence_summary_hash),
        to_kernel_digest(payload.policy.policy_hash),
        trace_hash,
        ink_core::ParentHashes::new(),
    );
    projected.seal().map_err(HostError::from)
}

#[allow(dead_code)]
fn kernel_projection_issuer_id(key_id: &str) -> Result<IssuerId, HostError> {
    let key_hash = sha256(key_id.as_bytes());
    let compact = format!("issuer:{}", hex::encode(&key_hash.0[..16]));
    IssuerId::from_str(&compact).map_err(HostError::from)
}

#[allow(dead_code)]
fn kernel_projection_claim_hash(
    receipt: &ReceiptJson,
    payload: &ReceiptPayload<'_>,
) -> Result<KernelDigest, HostError> {
    let mut parts = Vec::with_capacity(4 + receipt.reason_codes.len());
    parts.push(payload.action_id.as_bytes());
    parts.push(receipt.decision.as_bytes());
    parts.push(receipt.facts.risk_class.as_bytes());
    parts.push(receipt.policy.id.as_bytes());
    for reason in &receipt.reason_codes {
        parts.push(reason.as_bytes());
    }
    ink_core::hash::hash_many_labeled(b"compat-v2.claim", &parts).map_err(HostError::from)
}

fn sign_comparison_packet(
    left: &ReceiptJson,
    right: &ReceiptJson,
    out: &ComparisonOut,
) -> Result<SigningJson, HostError> {
    let issuer = ensure_local_issuer()?;
    let mut sink = Sha256Sink::new();
    let _ = write_tlv(&mut sink, 1, left.receipt_id.as_bytes());
    let _ = write_tlv(&mut sink, 2, right.receipt_id.as_bytes());
    let _ = write_tlv(&mut sink, 3, &[u8::from(out.decision_match)]);
    let _ = write_tlv(&mut sink, 4, &[u8::from(out.action_match)]);
    let _ = write_tlv(&mut sink, 5, &[u8::from(out.manifest_match)]);
    let digest = sink.finalize();
    let sign_result = issuer.sign_digest(&digest)?;
    Ok(SigningJson {
        transcript_encoding: "INK-COMPARISON-CORE-V1".to_string(),
        payload_hash: digest_json(&digest),
        algorithm: "Ed25519".to_string(),
        key_id: issuer.key_id.clone(),
        signature: Base64UrlUnpadded::encode_string(&sign_result.signature),
    })
}

fn verify_legacy_v1(receipt_path: &Path, value: &Value) -> Result<Value, HostError> {
    let integrity = value
        .get("integrity")
        .and_then(Value::as_object)
        .ok_or_else(|| HostError::InvalidInput("legacy receipt missing integrity".to_string()))?;
    let mut unsigned = value.clone();
    if let Some(map) = unsigned.as_object_mut() {
        map.remove("integrity");
    }
    let canonical = canonicalize_legacy(&unsigned);
    let expected_hash = format!("sha256:{}", hex::encode(Sha256::digest(&canonical)));
    let mut signer_input = canonical.clone();
    signer_input.extend_from_slice(LEGACY_DEV_SECRET);
    let full_signature = hex::encode(Sha512::digest(&signer_input));
    let expected_signature = format!("dev-signature:{}", &full_signature[..64]);
    let valid = integrity.get("hash").and_then(Value::as_str) == Some(expected_hash.as_str())
        && integrity.get("signature").and_then(Value::as_str) == Some(expected_signature.as_str());
    Ok(json!({
        "action_id": "unknown",
        "receipt_path": receipt_path,
        "manifest_path": Value::Null,
        "decision": value.get("gate").and_then(|gate| gate.get("decision")).and_then(Value::as_str).unwrap_or("unknown"),
        "summary": {
            "receipt_id": value.get("receipt_id").and_then(Value::as_str).unwrap_or("unknown"),
        },
        "verification": {
            "receipt_version": "v1",
            "scope": "legacy-v1-integrity",
            "overall": if valid { "legacy-valid" } else { "fail" },
            "issuer_key_id": Value::Null,
            "checks": [
                {
                    "id": "legacy.structure",
                    "status": if valid { "pass" } else { "fail" },
                    "reason_code": if valid { "LEGACY_V1_STRUCTURE_VALID" } else { "RECEIPT_SIGNATURE_INVALID" },
                },
                {
                    "id": "issuer.trust",
                    "status": "not_performed",
                    "reason_code": "LEGACY_V1_HAS_NO_V2_ISSUER_TRUST",
                }
            ],
        },
        "report": format!(
            "Verification for {}\nReceipt version: v1\nVerification scope: legacy-v1-integrity\nOverall: {}",
            receipt_path.display(),
            if valid { "legacy-valid" } else { "fail" },
        )
    }))
}

fn ensure_local_issuer() -> Result<LocalIssuer, HostError> {
    let root = config_root()?;
    fs::create_dir_all(&root)?;
    let _ = migrate_legacy_trust_policy(&root)?;
    if let Ok(config) = load_signer_config() {
        return load_issuer_from_config(&root, &config);
    }

    let keys_dir = root.join("keys");
    fs::create_dir_all(&keys_dir)?;
    let secret_path = keys_dir.join(ACTIVE_SECRET_FILE);
    let public_path = keys_dir.join(ACTIVE_PUBLIC_FILE);
    let (secret_key, public_key) = if secret_path.exists() && public_path.exists() {
        (
            decode_fixed::<32>(&fs::read_to_string(&secret_path)?)?,
            decode_fixed::<32>(&fs::read_to_string(&public_path)?)?,
        )
    } else {
        let mut rng = rand::rng();
        let mut secret_key = [0u8; 32];
        rng.fill_bytes(&mut secret_key);
        let signing_key = SigningKey::from_bytes(&secret_key);
        let public_key = signing_key.verifying_key().to_bytes();
        write_private_key(&secret_path, &secret_key)?;
        fs::write(&public_path, Base64UrlUnpadded::encode_string(&public_key))?;
        (secret_key, public_key)
    };

    let key_id = key_id_for_public(&public_key);
    let config = default_signer_config(&key_id);
    write_json(&root.join(SIGNER_CONFIG_FILE), &config)?;
    ensure_registry_entry(&root, &config, &public_key)?;
    ensure_signed_revocation_list(&root, &config, &secret_key, &public_key, &key_id)?;
    load_issuer_from_config(&root, &config)
}

fn load_signer_config() -> Result<SignerConfigJson, HostError> {
    let root = config_root()?;
    let path = root.join(SIGNER_CONFIG_FILE);
    let config: SignerConfigJson = serde_json::from_str(&fs::read_to_string(path)?)?;
    Ok(config)
}

#[allow(dead_code)]
fn load_trusted_key(key_id: &str, issuer_name: &str) -> Result<TrustedIssuerJson, HostError> {
    let registry = load_trust_registry()?;
    registry
        .issuers
        .into_iter()
        .find(|entry| {
            entry.key_id == key_id && entry.status == "active" && entry.issuer_name == issuer_name
        })
        .ok_or_else(|| HostError::Trust(format!("unknown trusted key {key_id}")))
}

fn default_signer_config(key_id: &str) -> SignerConfigJson {
    SignerConfigJson {
        schema: "ink.signer-config.v1".to_string(),
        backend: "demo_file".to_string(),
        issuer_name: LOCAL_ISSUER_NAME.to_string(),
        key_id: key_id.to_string(),
        secret_key_path: format!("keys/{ACTIVE_SECRET_FILE}"),
        public_key_path: format!("keys/{ACTIVE_PUBLIC_FILE}"),
        trust_registry_path: TRUST_REGISTRY_FILE.to_string(),
        revocation_list_path: REVOCATION_LIST_FILE.to_string(),
        receipt_encoding: RECEIPT_ENCODING_TLV_V2.to_string(),
        signer_base_url: None,
        auth_mode: None,
        auth_audience: None,
        request_timeout_ms: None,
        trust_registry_url: None,
        revocations_url: None,
        pinned_trust_authority_public_key: None,
    }
}

fn resolve_config_path(root: &Path, relative: &str) -> PathBuf {
    root.join(relative)
}

fn write_private_key(path: &Path, secret_key: &[u8; 32]) -> Result<(), HostError> {
    #[cfg(unix)]
    {
        use std::os::unix::fs::OpenOptionsExt;
        let mut file = std::fs::OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .mode(0o600)
            .open(path)?;
        file.write_all(Base64UrlUnpadded::encode_string(secret_key).as_bytes())?;
        file.flush()?;
        Ok(())
    }
    #[cfg(not(unix))]
    {
        fs::write(path, Base64UrlUnpadded::encode_string(secret_key))?;
        Ok(())
    }
}

fn load_issuer_from_config(
    root: &Path,
    config: &SignerConfigJson,
) -> Result<LocalIssuer, HostError> {
    if config.backend == "remote_kms_v1" {
        return load_remote_issuer_from_config(config);
    }
    let secret_path = resolve_config_path(root, &config.secret_key_path);
    let public_path = resolve_config_path(root, &config.public_key_path);
    let secret_key = decode_fixed::<32>(&fs::read_to_string(&secret_path)?)?;
    let public_key = decode_fixed::<32>(&fs::read_to_string(&public_path)?)?;
    let derived_key_id = key_id_for_public(&public_key);
    if config.key_id != derived_key_id {
        return Err(HostError::Trust(format!(
            "signer config key_id {} does not match the configured public key",
            config.key_id
        )));
    }
    ensure_registry_entry(root, config, &public_key)?;
    ensure_signed_revocation_list(root, config, &secret_key, &public_key, &config.key_id)?;
    Ok(LocalIssuer {
        public_key,
        key_id: config.key_id.clone(),
        issuer_name: config.issuer_name.clone(),
        backend: config.backend.clone(),
        receipt_encoding: config.receipt_encoding.clone(),
        signer_backend: SignerBackend::LocalEd25519 {
            secret_key,
            requires_demo_consent: config.backend == "demo_file",
        },
    })
}

fn load_remote_issuer_from_config(config: &SignerConfigJson) -> Result<LocalIssuer, HostError> {
    let trust_registry_url = config.trust_registry_url.as_deref().ok_or_else(|| {
        HostError::InvalidInput("remote_kms_v1 requires trust_registry_url".to_string())
    })?;
    let registry: TrustRegistryV2Json = Client::builder()
        .timeout(std::time::Duration::from_millis(
            config.request_timeout_ms.unwrap_or(5_000),
        ))
        .build()?
        .get(trust_registry_url)
        .send()?
        .error_for_status()?
        .json()?;
    if registry.schema != "ink.trust-registry.v2" {
        return Err(HostError::Trust(format!(
            "remote trust registry must use ink.trust-registry.v2, got {}",
            registry.schema
        )));
    }
    if let Some(pinned) = config.pinned_trust_authority_public_key.as_deref() {
        if !verify_trust_registry_signature_v2(&registry, pinned)? {
            return Err(HostError::Trust(
                "remote trust registry signature verification failed".to_string(),
            ));
        }
    }
    let issuer = registry
        .issuers
        .iter()
        .find(|entry| {
            entry.key_id == config.key_id
                && entry.issuer_name == config.issuer_name
                && entry.usage == "receipt_signing"
                && matches!(entry.state.as_str(), "active" | "retired")
        })
        .ok_or_else(|| {
            HostError::Trust(format!(
                "remote trust registry missing receipt_signing issuer {}",
                config.key_id
            ))
        })?;
    Ok(LocalIssuer {
        public_key: decode_fixed::<32>(&issuer.public_key)?,
        key_id: config.key_id.clone(),
        issuer_name: config.issuer_name.clone(),
        backend: config.backend.clone(),
        receipt_encoding: config.receipt_encoding.clone(),
        signer_backend: SignerBackend::RemoteKmsV1(RemoteSignerBackend {
            base_url: config.signer_base_url.clone().ok_or_else(|| {
                HostError::InvalidInput("remote_kms_v1 requires signer_base_url".to_string())
            })?,
            auth_mode: config.auth_mode.clone(),
            auth_audience: config.auth_audience.clone(),
            request_timeout_ms: config.request_timeout_ms.unwrap_or(5_000),
        }),
    })
}

fn migrate_legacy_trust_policy(root: &Path) -> Result<bool, HostError> {
    let legacy_path = root.join(LEGACY_TRUST_POLICY_FILE);
    if !legacy_path.exists() {
        return Ok(false);
    }

    let mut migrated = false;
    let registry_path = root.join(TRUST_REGISTRY_FILE);
    if !registry_path.exists() {
        let legacy: LegacyTrustPolicyJson =
            serde_json::from_str(&fs::read_to_string(&legacy_path)?)?;
        let mut issuers = Vec::new();
        for key in legacy.trusted_keys {
            issuers.push(TrustedIssuerJson {
                key_id: key.key_id,
                algorithm: key.algorithm,
                public_key: key.public_key,
                issuer_name: key
                    .issuer_names
                    .first()
                    .cloned()
                    .unwrap_or_else(|| LOCAL_ISSUER_NAME.to_string()),
                org_name: "BLKBX Lab".to_string(),
                status: key.status,
            });
        }
        write_json(
            &registry_path,
            &TrustRegistryJson {
                schema: "ink.trust-registry.v1".to_string(),
                issuers,
            },
        )?;
        migrated = true;
    }

    let signer_config_path = root.join(SIGNER_CONFIG_FILE);
    if !signer_config_path.exists() {
        let public_path = root.join("keys").join(ACTIVE_PUBLIC_FILE);
        if public_path.exists() {
            let public_key = decode_fixed::<32>(&fs::read_to_string(public_path)?)?;
            let key_id = key_id_for_public(&public_key);
            let mut config = default_signer_config(&key_id);
            if registry_path.exists() {
                let registry: TrustRegistryJson =
                    serde_json::from_str(&fs::read_to_string(&registry_path)?)?;
                if let Some(entry) = registry
                    .issuers
                    .iter()
                    .find(|entry| entry.key_id == key_id && entry.status == "active")
                {
                    config.issuer_name = entry.issuer_name.clone();
                }
            }
            write_json(&signer_config_path, &config)?;
            migrated = true;
        }
    }

    Ok(migrated)
}

#[allow(dead_code)]
fn load_trust_registry() -> Result<TrustRegistryJson, HostError> {
    let root = config_root()?;
    let path = root.join(TRUST_REGISTRY_FILE);
    let registry: TrustRegistryJson = serde_json::from_str(&fs::read_to_string(path)?)?;
    Ok(registry)
}

fn ensure_registry_entry(
    root: &Path,
    config: &SignerConfigJson,
    public_key: &[u8; 32],
) -> Result<(), HostError> {
    let path = resolve_config_path(root, &config.trust_registry_path);
    let mut registry = if path.exists() {
        serde_json::from_str::<TrustRegistryJson>(&fs::read_to_string(&path)?)?
    } else {
        TrustRegistryJson {
            schema: "ink.trust-registry.v1".to_string(),
            issuers: Vec::new(),
        }
    };
    if !registry
        .issuers
        .iter()
        .any(|entry| entry.key_id == config.key_id && entry.issuer_name == config.issuer_name)
    {
        registry.issuers.push(TrustedIssuerJson {
            key_id: config.key_id.clone(),
            algorithm: "Ed25519".to_string(),
            public_key: Base64UrlUnpadded::encode_string(public_key),
            issuer_name: config.issuer_name.clone(),
            org_name: "BLKBX Lab".to_string(),
            status: "active".to_string(),
        });
        write_json(&path, &registry)?;
    }
    Ok(())
}

fn ensure_signed_revocation_list(
    root: &Path,
    config: &SignerConfigJson,
    secret_key: &[u8; 32],
    public_key: &[u8; 32],
    key_id: &str,
) -> Result<(), HostError> {
    let path = resolve_config_path(root, &config.revocation_list_path);
    if path.exists() {
        return Ok(());
    }
    let mut list = RevocationListJson {
        schema: "ink.revocations.v1".to_string(),
        revoked_keys: Vec::new(),
        signing: SigningJson {
            transcript_encoding: REVOCATION_ENCODING_JSON_V1.to_string(),
            payload_hash: DigestJson {
                algorithm: "sha-256".to_string(),
                digest: String::new(),
            },
            algorithm: "Ed25519".to_string(),
            key_id: key_id.to_string(),
            signature: String::new(),
        },
    };
    let digest = revocation_list_digest(&list)?;
    let signing_key = SigningKey::from_bytes(secret_key);
    let signature = signing_key.sign(&digest.0);
    list.signing.payload_hash = digest_json(&digest);
    list.signing.signature = Base64UrlUnpadded::encode_string(&signature.to_bytes());
    write_json(&path, &list)?;
    ensure_registry_entry(root, config, public_key)?;
    Ok(())
}

#[allow(dead_code)]
fn ensure_key_not_revoked(key_id: &str) -> Result<(), HostError> {
    let list = load_revocation_list()?;
    if list.revoked_keys.iter().any(|entry| entry.key_id == key_id) {
        return Err(HostError::Trust(format!("trusted key {key_id} is revoked")));
    }
    Ok(())
}

#[allow(dead_code)]
fn load_revocation_list() -> Result<RevocationListJson, HostError> {
    let root = config_root()?;
    let path = root.join(REVOCATION_LIST_FILE);
    let list: RevocationListJson = serde_json::from_str(&fs::read_to_string(path)?)?;
    let trusted = load_trust_registry()?
        .issuers
        .into_iter()
        .find(|entry| entry.key_id == list.signing.key_id && entry.status == "active")
        .ok_or_else(|| {
            HostError::Trust(format!("unknown revocation signer {}", list.signing.key_id))
        })?;
    let digest = revocation_list_digest(&list)?;
    let payload_hash = digest_json(&digest);
    if payload_hash.digest != list.signing.payload_hash.digest
        || payload_hash.algorithm != list.signing.payload_hash.algorithm
    {
        return Err(HostError::Trust(
            "revocation list payload hash mismatch".to_string(),
        ));
    }
    let signature_valid = verify_ed25519_message_hash_bytes(
        &digest.0,
        &decode_fixed::<64>(&list.signing.signature)?,
        &decode_fixed::<32>(&trusted.public_key)?,
    )
    .map_err(|err| {
        HostError::Trust(format!("revocation signature verification failed: {err:?}"))
    })?;
    if !signature_valid {
        return Err(HostError::Trust(
            "revocation list signature mismatch".to_string(),
        ));
    }
    Ok(list)
}

fn revocation_list_digest(list: &RevocationListJson) -> Result<Sha256Digest, HostError> {
    let mut value = serde_json::to_value(list)?;
    if let Some(map) = value.as_object_mut() {
        map.remove("signing");
    }
    Ok(sha256(&canonicalize_legacy(&value)))
}

fn trust_registry_digest_v2(list: &TrustRegistryV2Json) -> Result<Sha256Digest, HostError> {
    let mut value = serde_json::to_value(list)?;
    if let Some(map) = value.as_object_mut() {
        map.remove("signing");
    }
    Ok(sha256(&canonicalize_legacy(&value)))
}

fn verify_trust_registry_signature_v2(
    registry: &TrustRegistryV2Json,
    pinned_public_key: &str,
) -> Result<bool, HostError> {
    let digest = trust_registry_digest_v2(registry)?;
    let expected_payload_hash = digest_json(&digest);
    if registry.signing.payload_hash.algorithm != expected_payload_hash.algorithm
        || registry.signing.payload_hash.digest != expected_payload_hash.digest
    {
        return Ok(false);
    }
    if registry.signing.algorithm != "Ed25519"
        || registry.signing.transcript_encoding != "INK-TRUST-REGISTRY-JSON-V2"
    {
        return Ok(false);
    }
    Ok(verify_ed25519_message_hash_bytes(
        &digest.0,
        &decode_fixed::<64>(&registry.signing.signature)?,
        &decode_fixed::<32>(pinned_public_key)?,
    )
    .unwrap_or(false))
}

fn receipt_digest_for_encoding(
    receipt: &ReceiptJson,
    payload: &ReceiptPayload<'_>,
    encoding: &str,
) -> Result<Sha256Digest, HostError> {
    match encoding {
        RECEIPT_ENCODING_TLV_V2 => receipt_transcript_hash(payload).map_err(HostError::from),
        RECEIPT_ENCODING_TLV_V1_LEGACY => {
            receipt_transcript_hash_legacy_v1(payload).map_err(HostError::from)
        }
        RECEIPT_ENCODING_JSON_CANONICAL_V1 => {
            let mut value = serde_json::to_value(receipt)?;
            if let Some(map) = value.as_object_mut() {
                map.remove("signing");
            }
            Ok(sha256(&canonicalize_legacy(&value)))
        }
        other => Err(HostError::InvalidInput(format!(
            "unsupported receipt transcript encoding {other}"
        ))),
    }
}

fn config_root() -> Result<PathBuf, HostError> {
    if let Ok(path) = env::var("INKRECEIPTS_CONFIG_DIR") {
        return Ok(PathBuf::from(path));
    }
    Ok(config_dir()
        .ok_or_else(|| HostError::InvalidInput("no config directory".to_string()))?
        .join(CONFIG_DIR_NAME))
}

fn hash_manifest(manifest: &ManifestJson) -> Result<Sha256Digest, HostError> {
    let action_id = leak_action_id(manifest.action_id.clone())?;
    let refs = manifest
        .artifacts
        .iter()
        .map(|artifact| {
            Ok(ArtifactRef {
                artifact_type: artifact_type_from_str(&artifact.artifact_type)?,
                media_type: media_type_from_str(&artifact.media_type)?,
                path_hash: sha256(artifact.path.as_bytes()),
                size_bytes: artifact.size_bytes,
                content_hash: parse_digest(&artifact.hash)?,
                schema_hash: artifact
                    .schema
                    .as_ref()
                    .map(|schema| sha256(schema.id.as_bytes())),
                path_hint: leak_bounded::<{ limits::MAX_PATH_HINT_LEN }>(artifact.path.clone())?,
            })
        })
        .collect::<Result<Vec<_>, HostError>>()?;
    let binding = ManifestBinding {
        action_id,
        manifest_hash: Sha256Digest::ZERO,
        artifacts: Box::leak(refs.into_boxed_slice()),
    };
    binding.validate()?;
    let mut sink = Sha256Sink::new();
    let _ = write_tlv(&mut sink, 1, binding.action_id.as_bytes());
    for artifact in binding.artifacts {
        let _ = write_tlv(&mut sink, 2, &artifact.content_hash.0);
        let _ = write_tlv(&mut sink, 3, &artifact.path_hash.0);
        let _ = write_tlv(&mut sink, 4, &artifact.size_bytes.to_be_bytes());
    }
    Ok(sink.finalize())
}

fn hash_evidence_summary(manifest: &ManifestJson) -> Result<Sha256Digest, HostError> {
    let mut sink = Sha256Sink::new();
    for artifact in &manifest.artifacts {
        let _ = write_tlv(&mut sink, 1, artifact.hash.digest.as_bytes());
        let _ = write_tlv(&mut sink, 2, artifact.path.as_bytes());
    }
    Ok(sink.finalize())
}

fn hash_controls_summary(controls: &[ControlObservation]) -> Sha256Digest {
    let mut sink = Sha256Sink::new();
    for control in controls {
        let _ = write_tlv(&mut sink, 1, &control.action_hash.0);
        let _ = write_tlv(&mut sink, 2, &(control.control_type as u8).to_be_bytes());
        let _ = write_tlv(&mut sink, 3, &(control.status as u8).to_be_bytes());
        let _ = write_tlv(&mut sink, 4, &control.actor_hash.0);
    }
    sink.finalize()
}

fn hosted_model_json(
    request: &HostedReceiptIssueRequest,
    body_bytes: &[u8],
    metadata_bytes: &[u8],
) -> ModelWaistJson {
    let body_hash = digest_json(&sha256(body_bytes));
    let metadata_hash = digest_json(&sha256(metadata_bytes));
    let action_hash = digest_json(&sha256(request.action_id.as_bytes()));
    let schema_hash = digest_json(&sha256(request.schema_key.as_bytes()));
    let workflow_hash = digest_json(&sha256(request.workflow_kind.as_bytes()));
    ModelWaistJson {
        schema: "ink.model-waist.v1".to_string(),
        identity: ModelIdentityJson {
            model_class: "hosted_api".to_string(),
            model_ref_hash: digest_json(&sha256(b"blkbx-lab:hosted-workflow")),
            model_slug: "hosted-workflow".to_string(),
            identity_evidence: IdentityEvidenceJson::Declared,
        },
        invocation: ModelInvocationJson {
            action_hash,
            messages_hash: body_hash.clone(),
            system_prompt_hash: None,
            tool_spec_hash: None,
            response_schema_hash: Some(schema_hash.clone()),
            parameters_hash: metadata_hash.clone(),
            requested_output: RequestedOutputJson::JsonSchema { schema_hash },
        },
        observation: ModelObservationJson {
            output_text_hash: None,
            structured_output_hash: Some(body_hash),
            provider_metadata_hash: Some(metadata_hash),
            finish_reason: "stop".to_string(),
            usage: TokenUsageJson {
                input_tokens: None,
                output_tokens: None,
                total_tokens: None,
            },
        },
        runtime: RuntimeJson {
            runtime_kind: "hosted_model_gateway".to_string(),
            execution_topology: "remote_gateway".to_string(),
            replay_strength: "declared_only".to_string(),
            determinism: RuntimeDeterminismJson {
                deterministic: false,
                seed_bound: false,
            },
            isolation: RuntimeIsolationJson {
                process_isolated: true,
            },
            provider_routing: ProviderRoutingJson {
                fallbacks_allowed: false,
                provider_pinned: true,
                data_collection_policy: "declared_deny".to_string(),
            },
        },
        plugin: PluginJson {
            plugin_id_hash: workflow_hash,
            plugin_version_hash: digest_json(&sha256(request.schema_version.as_bytes())),
            plugin_api_version: "v1".to_string(),
            maintainer_class: "first_party_reference".to_string(),
            normalization: NormalizationJson {
                input_normalized: true,
                output_normalized: true,
                raw_request_preserved: true,
                raw_response_preserved: false,
                secrets_redacted: true,
            },
            plugin_manifest_hash: digest_json(&sha256(b"blkbx-lab:hosted-workflow-plugin")),
            plugin_id_hint: request.workflow_kind.clone(),
            trust_level: "first_party_reference".to_string(),
        },
    }
}

fn canonicalize_legacy(value: &Value) -> Vec<u8> {
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
        Value::String(string) => serde_json::to_string(string)
            .unwrap_or_else(|_| "\"\"".to_string())
            .into_bytes(),
        Value::Array(items) => {
            let mut out = vec![b'['];
            for (index, item) in items.iter().enumerate() {
                if index > 0 {
                    out.push(b',');
                }
                out.extend_from_slice(&canonicalize_legacy(item));
            }
            out.push(b']');
            out
        }
        Value::Object(map) => {
            let ordered: BTreeMap<_, _> = map.iter().collect();
            let mut out = vec![b'{'];
            for (index, (key, item)) in ordered.iter().enumerate() {
                if index > 0 {
                    out.push(b',');
                }
                out.extend_from_slice(
                    serde_json::to_string(key)
                        .unwrap_or_else(|_| "\"\"".to_string())
                        .as_bytes(),
                );
                out.push(b':');
                out.extend_from_slice(&canonicalize_legacy(item));
            }
            out.push(b'}');
            out
        }
    }
}

fn safe_relative_path(raw: &str) -> Result<&Path, HostError> {
    let path = Path::new(raw);
    if path.is_absolute() {
        return Err(HostError::UnsafePath(raw.to_string()));
    }
    for component in path.components() {
        match component {
            Component::Normal(_) => {}
            _ => return Err(HostError::UnsafePath(raw.to_string())),
        }
    }
    Ok(path)
}

fn resolve_rooted_path(root: &Path, relative: &Path) -> Result<PathBuf, HostError> {
    let candidate = root.join(relative);
    let canonical_root = root.canonicalize()?;
    let canonical = candidate.canonicalize()?;
    if !canonical.starts_with(&canonical_root) {
        return Err(HostError::UnsafePath(candidate.display().to_string()));
    }
    let mut cursor = root.to_path_buf();
    for component in relative.components() {
        cursor.push(component);
        if fs::symlink_metadata(&cursor)?.file_type().is_symlink() {
            return Err(HostError::UnsafePath(cursor.display().to_string()));
        }
    }
    Ok(canonical)
}

fn write_json<T: Serialize>(path: &Path, value: &T) -> Result<(), HostError> {
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?;
    }
    let tmp = path.with_extension("tmp");
    let mut file = File::create(&tmp)?;
    file.write_all(serde_json::to_string_pretty(value)?.as_bytes())?;
    file.flush()?;
    fs::rename(tmp, path)?;
    Ok(())
}

fn parse_digest(value: &DigestJson) -> Result<Sha256Digest, HostError> {
    parse_hex_digest(&value.digest)
}

#[allow(dead_code)]
fn to_kernel_digest(value: Sha256Digest) -> KernelDigest {
    KernelDigest(value.0)
}

fn parse_hex_digest(value: &str) -> Result<Sha256Digest, HostError> {
    let bytes = hex::decode(value)
        .map_err(|_| HostError::InvalidInput(format!("invalid digest {value}")))?;
    let array: [u8; 32] = bytes
        .try_into()
        .map_err(|_| HostError::InvalidInput(format!("invalid digest {value}")))?;
    Ok(Sha256Digest(array))
}

fn decode_fixed<const N: usize>(value: &str) -> Result<[u8; N], HostError> {
    let bytes = Base64UrlUnpadded::decode_vec(value)
        .map_err(|_| HostError::InvalidInput("invalid base64".to_string()))?;
    bytes
        .try_into()
        .map_err(|_| HostError::InvalidInput("invalid fixed length".to_string()))
}

fn leak_bounded<const N: usize>(value: String) -> Result<BoundedBytes<'static, N>, HostError> {
    let leaked = Box::leak(value.into_boxed_str());
    BoundedBytes::new(leaked.as_bytes()).map_err(HostError::from)
}

fn leak_action_id(value: String) -> Result<ActionId<'static>, HostError> {
    let leaked = Box::leak(value.into_boxed_str());
    BoundedBytes::new_identifier(leaked.as_bytes()).map_err(HostError::from)
}

fn leak_receipt_id(value: String) -> Result<ReceiptId<'static>, HostError> {
    let leaked = Box::leak(value.into_boxed_str());
    BoundedBytes::new_identifier(leaked.as_bytes()).map_err(HostError::from)
}

fn leak_key_id(value: String) -> Result<KeyId<'static>, HostError> {
    let leaked = Box::leak(value.into_boxed_str());
    BoundedBytes::new_identifier(leaked.as_bytes()).map_err(HostError::from)
}

fn leak_reason(
    value: String,
) -> Result<BoundedBytes<'static, { limits::MAX_REASON_CODE_LEN }>, HostError> {
    let leaked = Box::leak(value.into_boxed_str());
    BoundedBytes::new_reason_code(leaked.as_bytes()).map_err(HostError::from)
}

fn facts_json(facts: PolicyFacts) -> PolicyFactsJson {
    PolicyFactsJson {
        risk_class: public_risk_class(facts.risk_class).to_string(),
        requires_human_review: facts.requires_human_review,
        binding_effect_present: facts.binding_effect_present,
        provider_fallbacks_allowed: facts.provider_fallbacks_allowed,
        plugin_trust_level: public_plugin_trust(facts.plugin_trust_level).to_string(),
        runtime_kind: public_runtime_kind(facts.runtime_kind).to_string(),
        replay_strength: public_replay_strength(facts.replay_strength).to_string(),
        model_class: public_model_class(facts.model_class).to_string(),
    }
}

fn digest_json(value: &Sha256Digest) -> DigestJson {
    DigestJson {
        algorithm: "sha-256".to_string(),
        digest: hex::encode(value.0),
    }
}

fn now_timestamp() -> TimestampUtc {
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default();
    let nanos = now.subsec_nanos();
    debug_assert!(nanos < 1_000_000_000);
    TimestampUtc {
        unix_seconds: now.as_secs() as i64,
        nanos,
    }
}

fn sibling_manifest(receipt_path: &Path) -> Option<PathBuf> {
    let candidate = receipt_path.parent()?.join("ink_manifest.v2.json");
    candidate.exists().then_some(candidate)
}

fn sibling_controls(manifest_path: &Path) -> Option<PathBuf> {
    let candidate = manifest_path.parent()?.join("controls.supplied.json");
    candidate.exists().then_some(candidate)
}

fn has_human_review(controls: &[ControlObservation]) -> bool {
    controls.iter().any(|control| {
        control.control_type == ControlType::HumanReview
            && matches!(
                control.status,
                ControlStatus::Approved | ControlStatus::Present
            )
    })
}

fn key_id_for_public(public_key: &[u8; 32]) -> String {
    format!("ed25519:{}", hex::encode(Sha256::digest(public_key)))
}

fn reason_strings(slots: &[ReasonCodeSlot<'_>]) -> Vec<String> {
    slots
        .iter()
        .map(|slot| String::from_utf8_lossy(slot.bytes).to_string())
        .collect()
}

fn public_decision(value: Decision) -> &'static str {
    match value {
        Decision::Pass => "pass",
        Decision::Warn => "warn",
        Decision::Escalate | Decision::Block => "fail",
    }
}

fn public_risk_class(value: RiskClass) -> &'static str {
    match value {
        RiskClass::Low => "low",
        RiskClass::Medium => "medium",
        RiskClass::High => "high",
    }
}

fn public_plugin_trust(value: PluginTrustFact) -> &'static str {
    match value {
        PluginTrustFact::Untrusted => "untrusted",
        PluginTrustFact::LocallyAllowed => "locally_allowed",
        PluginTrustFact::FirstPartyReference => "first_party_reference",
        PluginTrustFact::ThirdPartyTrusted => "third_party_trusted",
        PluginTrustFact::ReproduciblyBuilt => "reproducibly_built",
    }
}

#[cfg(test)]
mod tests;

fn public_runtime_kind(value: RuntimeKind) -> &'static str {
    match value {
        RuntimeKind::DeterministicDemo => "deterministic_demo",
        RuntimeKind::LocalOpenWeightModel => "local_open_weight_model",
        RuntimeKind::LocalClosedWeightModel => "local_closed_weight_model",
        RuntimeKind::HostedModelApi => "hosted_model_api",
        RuntimeKind::HostedModelGateway => "hosted_model_gateway",
        RuntimeKind::ExternalProcess => "external_process",
        RuntimeKind::ReplayOnly => "replay_only",
    }
}

fn public_replay_strength(value: ReplayStrength) -> &'static str {
    match value {
        ReplayStrength::FullyReplayable => "fully_replayable",
        ReplayStrength::InputWeightsConfigBound => "input_weights_config_bound",
        ReplayStrength::RequestResponseBound => "request_response_bound",
        ReplayStrength::DeclaredOnly => "declared_only",
        ReplayStrength::NotReplayable => "not_replayable",
    }
}

fn public_model_class(value: ModelClass) -> &'static str {
    match value {
        ModelClass::OpenWeight => "open_weight",
        ModelClass::ClosedWeight => "closed_weight",
        ModelClass::HostedApi => "hosted_api",
        ModelClass::Replay => "replay",
        ModelClass::DeterministicDemo => "deterministic_demo",
    }
}

fn policy_decision_from_str(value: &str) -> Result<Decision, HostError> {
    match value {
        "pass" => Ok(Decision::Pass),
        "warn" => Ok(Decision::Warn),
        "fail" => Ok(Decision::Block),
        _ => Err(HostError::InvalidInput(format!(
            "unknown policy decision {value}"
        ))),
    }
}

fn policy_decision_from_public(value: &str) -> Decision {
    match value {
        "pass" => Decision::Pass,
        "warn" => Decision::Warn,
        _ => Decision::Block,
    }
}

fn risk_class_from_str(value: &str) -> Result<RiskClass, HostError> {
    match value {
        "low" => Ok(RiskClass::Low),
        "medium" => Ok(RiskClass::Medium),
        "high" | "critical" => Ok(RiskClass::High),
        _ => Err(HostError::InvalidInput(format!(
            "unknown risk class {value}"
        ))),
    }
}

fn control_type_from_str(value: &str) -> Result<ControlType, HostError> {
    match value {
        "human_review" => Ok(ControlType::HumanReview),
        "approval" => Ok(ControlType::Approval),
        "dual_control" => Ok(ControlType::DualControl),
        "policy_exception" => Ok(ControlType::PolicyException),
        "supervisor_override" => Ok(ControlType::SupervisorOverride),
        "external_audit" => Ok(ControlType::ExternalAudit),
        _ => Err(HostError::InvalidInput(format!(
            "unknown control type {value}"
        ))),
    }
}

fn control_status_from_str(value: &str) -> Result<ControlStatus, HostError> {
    match value {
        "present" => Ok(ControlStatus::Present),
        "approved" => Ok(ControlStatus::Approved),
        "rejected" => Ok(ControlStatus::Rejected),
        "expired" => Ok(ControlStatus::Expired),
        "invalid" => Ok(ControlStatus::Invalid),
        _ => Err(HostError::InvalidInput(format!(
            "unknown control status {value}"
        ))),
    }
}

fn model_class_from_str(value: &str) -> Result<ModelClass, HostError> {
    match value {
        "open_weight" => Ok(ModelClass::OpenWeight),
        "closed_weight" => Ok(ModelClass::ClosedWeight),
        "hosted_api" => Ok(ModelClass::HostedApi),
        "replay" => Ok(ModelClass::Replay),
        "deterministic_demo" => Ok(ModelClass::DeterministicDemo),
        _ => Err(HostError::InvalidInput(format!(
            "unknown model class {value}"
        ))),
    }
}

fn runtime_kind_from_str(value: &str) -> Result<RuntimeKind, HostError> {
    match value {
        "deterministic_demo" => Ok(RuntimeKind::DeterministicDemo),
        "local_open_weight_model" => Ok(RuntimeKind::LocalOpenWeightModel),
        "local_closed_weight_model" => Ok(RuntimeKind::LocalClosedWeightModel),
        "hosted_model_api" => Ok(RuntimeKind::HostedModelApi),
        "hosted_model_gateway" => Ok(RuntimeKind::HostedModelGateway),
        "external_process" => Ok(RuntimeKind::ExternalProcess),
        "replay_only" => Ok(RuntimeKind::ReplayOnly),
        _ => Err(HostError::InvalidInput(format!(
            "unknown runtime kind {value}"
        ))),
    }
}

fn execution_topology_from_str(value: &str) -> Result<ExecutionTopology, HostError> {
    match value {
        "rule_based_local" => Ok(ExecutionTopology::RuleBasedLocal),
        "local_process" => Ok(ExecutionTopology::LocalProcess),
        "local_container" => Ok(ExecutionTopology::LocalContainer),
        "remote_provider" => Ok(ExecutionTopology::RemoteProvider),
        "remote_gateway" => Ok(ExecutionTopology::RemoteGateway),
        "external_subprocess" => Ok(ExecutionTopology::ExternalSubprocess),
        "replay_file" => Ok(ExecutionTopology::ReplayFile),
        _ => Err(HostError::InvalidInput(format!(
            "unknown execution topology {value}"
        ))),
    }
}

fn replay_strength_from_str(value: &str) -> Result<ReplayStrength, HostError> {
    match value {
        "fully_replayable" => Ok(ReplayStrength::FullyReplayable),
        "input_weights_config_bound" => Ok(ReplayStrength::InputWeightsConfigBound),
        "request_response_bound" => Ok(ReplayStrength::RequestResponseBound),
        "declared_only" => Ok(ReplayStrength::DeclaredOnly),
        "not_replayable" => Ok(ReplayStrength::NotReplayable),
        _ => Err(HostError::InvalidInput(format!(
            "unknown replay strength {value}"
        ))),
    }
}

fn data_collection_from_str(value: &str) -> DataCollectionPolicy {
    match value {
        "declared_allow" => DataCollectionPolicy::DeclaredAllow,
        "declared_deny" => DataCollectionPolicy::DeclaredDeny,
        _ => DataCollectionPolicy::Unknown,
    }
}

fn maintainer_class_from_str(value: &str) -> MaintainerClass {
    match value {
        "first_party_reference" => MaintainerClass::FirstPartyReference,
        "third_party" => MaintainerClass::ThirdParty,
        "user_local" => MaintainerClass::UserLocal,
        _ => MaintainerClass::Unknown,
    }
}

fn plugin_trust_from_str(value: &str) -> PluginTrustLevel {
    match value {
        "locally_allowed" => PluginTrustLevel::LocallyAllowed,
        "third_party_trusted" => PluginTrustLevel::ThirdPartyTrusted,
        "reproducibly_built" => PluginTrustLevel::ReproduciblyBuilt,
        "first_party_reference" => PluginTrustLevel::FirstPartyReference,
        _ => PluginTrustLevel::Untrusted,
    }
}

fn plugin_trust_fact(value: PluginTrustLevel) -> PluginTrustFact {
    match value {
        PluginTrustLevel::Untrusted => PluginTrustFact::Untrusted,
        PluginTrustLevel::LocallyAllowed => PluginTrustFact::LocallyAllowed,
        PluginTrustLevel::FirstPartyReference => PluginTrustFact::FirstPartyReference,
        PluginTrustLevel::ThirdPartyTrusted => PluginTrustFact::ThirdPartyTrusted,
        PluginTrustLevel::ReproduciblyBuilt => PluginTrustFact::ReproduciblyBuilt,
    }
}

fn plugin_trust_fact_from_str(value: &str) -> Result<PluginTrustFact, HostError> {
    Ok(plugin_trust_fact(plugin_trust_from_str(value)))
}

fn finish_reason_from_str(value: &str) -> FinishReason {
    match value {
        "stop" => FinishReason::Stop,
        "length" => FinishReason::Length,
        "tool_call" => FinishReason::ToolCall,
        "content_filter" => FinishReason::ContentFilter,
        "error" => FinishReason::Error,
        _ => FinishReason::Unknown,
    }
}

fn artifact_type_from_str(value: &str) -> Result<ArtifactType, HostError> {
    match value {
        "action_json" => Ok(ArtifactType::ActionProposal),
        "prompt_text" => Ok(ArtifactType::Prompt),
        "controls_json" => Ok(ArtifactType::ControlSet),
        "policy_json" => Ok(ArtifactType::PolicySpec),
        "policy_compilation_json" => Ok(ArtifactType::PolicyCompilation),
        _ => Ok(ArtifactType::Other),
    }
}

fn media_type_from_str(value: &str) -> Result<MediaType, HostError> {
    match value {
        "application/json" => Ok(MediaType::ApplicationJson),
        "text/plain; charset=utf-8" => Ok(MediaType::TextPlain),
        "application/yaml" => Ok(MediaType::ApplicationYaml),
        "application/octet-stream" => Ok(MediaType::ApplicationOctetStream),
        _ => Err(HostError::InvalidInput(format!(
            "unknown media type {value}"
        ))),
    }
}

struct LocalIssuer {
    public_key: [u8; 32],
    key_id: String,
    issuer_name: String,
    backend: String,
    receipt_encoding: String,
    signer_backend: SignerBackend,
}

enum SignerBackend {
    LocalEd25519 {
        secret_key: [u8; 32],
        requires_demo_consent: bool,
    },
    RemoteKmsV1(RemoteSignerBackend),
}

struct RemoteSignerBackend {
    base_url: String,
    auth_mode: Option<String>,
    auth_audience: Option<String>,
    request_timeout_ms: u64,
}

struct SignOperationResult {
    signature: [u8; 64],
    signer_request_id: Option<String>,
    trust_registry_version: Option<String>,
    revocation_version: Option<String>,
}

impl LocalIssuer {
    fn requires_demo_consent(&self) -> bool {
        matches!(
            self.signer_backend,
            SignerBackend::LocalEd25519 {
                requires_demo_consent: true,
                ..
            }
        )
    }

    fn sign_digest(&self, digest: &Sha256Digest) -> Result<SignOperationResult, HostError> {
        match &self.signer_backend {
            SignerBackend::LocalEd25519 { secret_key, .. } => {
                let signing_key = SigningKey::from_bytes(secret_key);
                Ok(SignOperationResult {
                    signature: signing_key.sign(&digest.0).to_bytes(),
                    signer_request_id: None,
                    trust_registry_version: None,
                    revocation_version: None,
                })
            }
            SignerBackend::RemoteKmsV1(remote) => remote.sign(
                &self.key_id,
                &self.issuer_name,
                &self.receipt_encoding,
                digest,
            ),
        }
    }
}

impl Drop for SignerBackend {
    fn drop(&mut self) {
        if let SignerBackend::LocalEd25519 { secret_key, .. } = self {
            for byte in secret_key {
                *byte = 0;
            }
        }
    }
}

impl RemoteSignerBackend {
    fn sign(
        &self,
        key_id: &str,
        issuer_name: &str,
        receipt_encoding: &str,
        digest: &Sha256Digest,
    ) -> Result<SignOperationResult, HostError> {
        let client = Client::builder()
            .timeout(std::time::Duration::from_millis(self.request_timeout_ms))
            .build()?;
        let request = RemoteSignRequest {
            key_id: key_id.to_string(),
            issuer_name: issuer_name.to_string(),
            algorithm: "Ed25519".to_string(),
            transcript_encoding: receipt_encoding.to_string(),
            payload_hash: digest_json(digest),
        };
        let mut builder = client.post(format!("{}/v1/signatures/ed25519", self.base_url));
        if self.auth_mode.as_deref() == Some("bearer") {
            if let Some(token) = self.auth_audience.as_ref() {
                builder = builder.bearer_auth(token);
            }
        }
        let response: RemoteSignResponse =
            builder.json(&request).send()?.error_for_status()?.json()?;
        let signature = decode_fixed::<64>(&response.signature)?;
        Ok(SignOperationResult {
            signature,
            signer_request_id: response.signer_request_id,
            trust_registry_version: response.trust_registry_version,
            revocation_version: response.revocation_version,
        })
    }
}
