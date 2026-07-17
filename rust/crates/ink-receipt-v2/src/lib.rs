use std::collections::BTreeMap;

use base64ct::{Base64UrlUnpadded, Encoding};
use ink_core::bounded::{DomainTag, IssuerId, SchemaAuthority, SchemaId};
use ink_core::controls::{ControlObservation, ControlStatus, ControlType};
use ink_core::digest::{sha256, write_tlv, Sha256Sink};
use ink_core::legacy::policy::{PluginTrustFact, PolicyFacts, ReasonCodeSlot, RiskClass};
use ink_core::legacy::receipt::{
    receipt_transcript_hash, receipt_transcript_hash_legacy_v1, IssuerClaim, PolicyBinding,
    ReceiptPayload, ReceiptProfile, ReceiptSchemaVersion,
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
    ActionId, BoundedBytes, Ed25519PublicKey, KeyId, ReceiptId, Sha256Digest, TimestampUtc,
};
use ink_core::{Digest as KernelDigest, ReceiptEnvelope};
use ink_verify::{verify_ed25519_message_hash_bytes, VerificationPolicy};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use thiserror::Error;

pub const RECEIPT_SCHEMA_V2: &str = "ink.receipt.v2";
pub const RECEIPT_PROFILE: &str = "thin_waist_v2";
pub const MANIFEST_SCHEMA_V2: &str = "ink.manifest.v2";
pub const CONTROLS_SCHEMA_V1: &str = "ink.controls.v1";
pub const TRUST_REGISTRY_SCHEMA_V1: &str = "ink.trust-registry.v1";
pub const REVOCATIONS_SCHEMA_V1: &str = "ink.revocations.v1";
pub const VERIFY_POLICY_SCHEMA_V1: &str = "ink.verify-policy.v1";
pub const VERIFICATION_REPORT_SCHEMA_V1: &str = "ink.verification-report.v1";
pub const RECEIPT_ENCODING_TLV_V2: &str = "INK-CORE-TLV-V2";
pub const RECEIPT_ENCODING_TLV_V1_LEGACY: &str = "INK-CORE-TRANSCRIPT-V1";
pub const RECEIPT_ENCODING_JSON_CANONICAL_V1: &str = "INK-CORE-JSON-CANONICAL-V1";
pub const REVOCATION_ENCODING_JSON_V1: &str = "INK-REVOCATION-JSON-V1";
pub const BANK_STRICT_POLICY_ID: &str = "BANK_STRICT_POLICY";
pub const HOST_COMPATIBILITY_POLICY_ID: &str = "HOST_COMPATIBILITY_POLICY";

#[derive(Debug, Error)]
pub enum ReceiptV2Error {
    #[error("json error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("core error: {0:?}")]
    Core(ink_core::error::Error),
    #[error("invalid input: {0}")]
    InvalidInput(String),
    #[error("trust error: {0}")]
    Trust(String),
}

impl From<ink_core::error::Error> for ReceiptV2Error {
    fn from(value: ink_core::error::Error) -> Self {
        Self::Core(value)
    }
}

pub type Result<T> = std::result::Result<T, ReceiptV2Error>;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct DigestJson {
    pub algorithm: String,
    pub digest: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SchemaJson {
    pub id: String,
    pub version: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ManifestArtifactJson {
    pub artifact_type: String,
    pub path: String,
    pub media_type: String,
    pub size_bytes: u64,
    pub hash: DigestJson,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub schema: Option<SchemaJson>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ManifestJson {
    pub schema: String,
    pub action_id: String,
    pub created_at: String,
    pub artifacts: Vec<ManifestArtifactJson>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ControlsFile {
    pub schema: String,
    pub observations: Vec<ControlObservationJson>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ControlObservationJson {
    pub control_type: String,
    pub action_hash: String,
    pub status: String,
    pub actor_hash: String,
    pub observed_at: i64,
    pub evidence_hash: Option<DigestJson>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ModelWaistJson {
    pub schema: String,
    pub identity: ModelIdentityJson,
    pub invocation: ModelInvocationJson,
    pub observation: ModelObservationJson,
    pub runtime: RuntimeJson,
    pub plugin: PluginJson,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ModelIdentityJson {
    pub model_class: String,
    pub model_ref_hash: DigestJson,
    pub model_slug: String,
    pub identity_evidence: IdentityEvidenceJson,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum IdentityEvidenceJson {
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

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ModelInvocationJson {
    pub action_hash: DigestJson,
    pub messages_hash: DigestJson,
    pub system_prompt_hash: Option<DigestJson>,
    pub tool_spec_hash: Option<DigestJson>,
    pub response_schema_hash: Option<DigestJson>,
    pub parameters_hash: DigestJson,
    pub requested_output: RequestedOutputJson,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum RequestedOutputJson {
    FreeText,
    JsonSchema { schema_hash: DigestJson },
    ToolCall { tool_spec_hash: DigestJson },
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ModelObservationJson {
    pub output_text_hash: Option<DigestJson>,
    pub structured_output_hash: Option<DigestJson>,
    pub provider_metadata_hash: Option<DigestJson>,
    pub finish_reason: String,
    pub usage: TokenUsageJson,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TokenUsageJson {
    pub input_tokens: Option<u32>,
    pub output_tokens: Option<u32>,
    pub total_tokens: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RuntimeJson {
    pub runtime_kind: String,
    pub execution_topology: String,
    pub replay_strength: String,
    pub determinism: RuntimeDeterminismJson,
    pub isolation: RuntimeIsolationJson,
    pub provider_routing: ProviderRoutingJson,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RuntimeDeterminismJson {
    pub deterministic: bool,
    pub seed_bound: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RuntimeIsolationJson {
    pub process_isolated: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ProviderRoutingJson {
    pub fallbacks_allowed: bool,
    pub provider_pinned: bool,
    pub data_collection_policy: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PluginJson {
    pub plugin_id_hash: DigestJson,
    pub plugin_version_hash: DigestJson,
    pub plugin_api_version: String,
    pub maintainer_class: String,
    pub normalization: NormalizationJson,
    pub plugin_manifest_hash: DigestJson,
    pub plugin_id_hint: String,
    pub trust_level: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct NormalizationJson {
    pub input_normalized: bool,
    pub output_normalized: bool,
    pub raw_request_preserved: bool,
    pub raw_response_preserved: bool,
    pub secrets_redacted: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct ReceiptJson {
    pub schema: String,
    pub receipt_id: String,
    pub receipt_profile: String,
    pub action_id: String,
    pub issued_at: i64,
    pub issuer: IssuerJson,
    pub manifest_hash: DigestJson,
    pub policy: PolicyBindingJson,
    pub runtime: RuntimeJson,
    pub model: ModelWaistJson,
    pub facts: PolicyFactsJson,
    pub decision: String,
    pub reason_codes: Vec<String>,
    pub evidence_summary_hash: DigestJson,
    pub controls_summary_hash: DigestJson,
    pub signing: SigningJson,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct IssuerJson {
    pub name: String,
    pub key_id: String,
    pub public_key: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PolicyBindingJson {
    pub id: String,
    pub version: String,
    pub hash: DigestJson,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PolicyFactsJson {
    pub risk_class: String,
    pub requires_human_review: bool,
    pub binding_effect_present: bool,
    pub provider_fallbacks_allowed: bool,
    pub plugin_trust_level: String,
    pub runtime_kind: String,
    pub replay_strength: String,
    pub model_class: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct SigningJson {
    pub transcript_encoding: String,
    pub payload_hash: DigestJson,
    pub algorithm: String,
    pub key_id: String,
    pub signature: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TrustRegistryJson {
    pub schema: String,
    pub issuers: Vec<TrustedIssuerJson>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct TrustedIssuerJson {
    pub key_id: String,
    pub algorithm: String,
    pub public_key: String,
    pub issuer_name: String,
    pub org_name: String,
    pub status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RevocationListJson {
    pub schema: String,
    pub revoked_keys: Vec<RevokedKeyJson>,
    pub signing: SigningJson,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct RevokedKeyJson {
    pub key_id: String,
    pub reason: String,
    pub revoked_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct VerifyPolicyJson {
    pub schema: String,
    pub policy_id: String,
    pub require_canonical_tlv_v2: bool,
    pub allow_verify_only_formats: bool,
    pub require_trusted_issuer: bool,
    pub require_revocation_check: bool,
    pub require_manifest_hash_match_when_manifest_present: bool,
    pub require_evidence_summary_match_when_manifest_present: bool,
    pub require_controls_summary_match_when_controls_present: bool,
    pub allow_network: bool,
}

impl VerifyPolicyJson {
    pub fn bank_strict() -> Self {
        Self {
            schema: VERIFY_POLICY_SCHEMA_V1.to_string(),
            policy_id: BANK_STRICT_POLICY_ID.to_string(),
            require_canonical_tlv_v2: true,
            allow_verify_only_formats: false,
            require_trusted_issuer: true,
            require_revocation_check: false,
            require_manifest_hash_match_when_manifest_present: true,
            require_evidence_summary_match_when_manifest_present: true,
            require_controls_summary_match_when_controls_present: true,
            allow_network: false,
        }
    }

    pub fn host_compatibility() -> Self {
        Self {
            schema: VERIFY_POLICY_SCHEMA_V1.to_string(),
            policy_id: HOST_COMPATIBILITY_POLICY_ID.to_string(),
            require_canonical_tlv_v2: false,
            allow_verify_only_formats: true,
            require_trusted_issuer: true,
            require_revocation_check: false,
            require_manifest_hash_match_when_manifest_present: true,
            require_evidence_summary_match_when_manifest_present: true,
            require_controls_summary_match_when_controls_present: true,
            allow_network: false,
        }
    }

    pub fn validate(&self) -> Result<()> {
        if self.schema != VERIFY_POLICY_SCHEMA_V1 {
            return Err(ReceiptV2Error::InvalidInput(format!(
                "expected {}",
                VERIFY_POLICY_SCHEMA_V1
            )));
        }
        if self.require_canonical_tlv_v2 && self.allow_verify_only_formats {
            return Err(ReceiptV2Error::InvalidInput(
                "strict canonical tlv policy cannot allow verify-only formats".to_string(),
            ));
        }
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct VerificationCheck {
    pub id: String,
    pub status: String,
    pub reason_code: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct VerificationReportJson {
    pub schema: String,
    pub status: String,
    pub code: String,
    pub transcript_encoding: String,
    pub receipt_profile: String,
    pub issuer: String,
    pub key_id: String,
    pub payload_digest_alg: String,
    pub payload_digest_hex: String,
    pub signature_valid: bool,
    pub trusted_issuer: bool,
    pub revocation_checked: bool,
    pub revocation_ok: bool,
    pub policy_accepted: bool,
    pub verification_engine: String,
    pub network_required: bool,
    pub scope: String,
    pub checks: Vec<VerificationCheck>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct RevocationOutcome {
    checked: bool,
    ok: bool,
    code: &'static str,
}

pub fn load_trust_registry(bytes: &[u8]) -> Result<TrustRegistryJson> {
    let registry: TrustRegistryJson = serde_json::from_slice(bytes)?;
    if registry.schema != TRUST_REGISTRY_SCHEMA_V1 {
        return Err(ReceiptV2Error::InvalidInput(format!(
            "expected {}",
            TRUST_REGISTRY_SCHEMA_V1
        )));
    }
    Ok(registry)
}

pub fn load_revocation_list(bytes: &[u8]) -> Result<RevocationListJson> {
    let list: RevocationListJson = serde_json::from_slice(bytes)?;
    if list.schema != REVOCATIONS_SCHEMA_V1 {
        return Err(ReceiptV2Error::InvalidInput(format!(
            "expected {}",
            REVOCATIONS_SCHEMA_V1
        )));
    }
    Ok(list)
}

pub fn load_verify_policy(bytes: &[u8]) -> Result<VerifyPolicyJson> {
    let policy: VerifyPolicyJson = serde_json::from_slice(bytes)?;
    policy.validate()?;
    Ok(policy)
}

pub fn verify_bundle(
    receipt_json: &[u8],
    manifest_json: Option<&[u8]>,
    controls_json: Option<&[u8]>,
    trust_registry_json: Option<&[u8]>,
    revocation_list_json: Option<&[u8]>,
    verify_policy_json: Option<&[u8]>,
    pinned_public_key: Option<&str>,
) -> Result<VerificationReportJson> {
    verify_receipt(
        receipt_json,
        manifest_json,
        controls_json,
        trust_registry_json,
        revocation_list_json,
        verify_policy_json,
        pinned_public_key,
    )
}

pub fn verify_receipt(
    receipt_json: &[u8],
    manifest_json: Option<&[u8]>,
    controls_json: Option<&[u8]>,
    trust_registry_json: Option<&[u8]>,
    revocation_list_json: Option<&[u8]>,
    verify_policy_json: Option<&[u8]>,
    pinned_public_key: Option<&str>,
) -> Result<VerificationReportJson> {
    let policy = verify_policy_json
        .map(load_verify_policy)
        .transpose()?
        .unwrap_or_else(VerifyPolicyJson::bank_strict);
    let registry = trust_registry_json.map(load_trust_registry).transpose()?;
    let revocations = revocation_list_json.map(load_revocation_list).transpose()?;
    verify_receipt_with_inputs(
        receipt_json,
        manifest_json,
        controls_json,
        registry.as_ref(),
        revocations.as_ref(),
        &policy,
        pinned_public_key,
    )
}

pub fn verify_receipt_with_registry(
    receipt_json: &[u8],
    manifest_json: Option<&[u8]>,
    controls_json: Option<&[u8]>,
    trust_registry: Option<&TrustRegistryJson>,
    revocation_list: Option<&RevocationListJson>,
    verify_policy: &VerifyPolicyJson,
    pinned_public_key: Option<&str>,
) -> Result<VerificationReportJson> {
    verify_receipt_with_inputs(
        receipt_json,
        manifest_json,
        controls_json,
        trust_registry,
        revocation_list,
        verify_policy,
        pinned_public_key,
    )
}

fn verify_receipt_with_inputs(
    receipt_json: &[u8],
    manifest_json: Option<&[u8]>,
    controls_json: Option<&[u8]>,
    trust_registry: Option<&TrustRegistryJson>,
    revocation_list: Option<&RevocationListJson>,
    verify_policy: &VerifyPolicyJson,
    pinned_public_key: Option<&str>,
) -> Result<VerificationReportJson> {
    let receipt: ReceiptJson = serde_json::from_slice(receipt_json)?;
    if receipt.schema != RECEIPT_SCHEMA_V2 {
        return Err(ReceiptV2Error::InvalidInput(format!(
            "expected {}",
            RECEIPT_SCHEMA_V2
        )));
    }

    let payload = receipt_payload_from_json(&receipt)?;
    let digest =
        receipt_digest_for_encoding(&receipt, &payload, &receipt.signing.transcript_encoding)?;
    let expected_payload_hash = digest_json(&digest);
    let payload_hash_valid = receipt.signing.payload_hash.algorithm
        == expected_payload_hash.algorithm
        && receipt.signing.payload_hash.digest == expected_payload_hash.digest;

    let trusted_issuer_entry = trust_registry.and_then(|registry| {
        registry.issuers.iter().find(|entry| {
            entry.key_id == receipt.signing.key_id
                && entry.issuer_name == receipt.issuer.name
                && entry.status == "active"
        })
    });
    let embedded_key = Ed25519PublicKey(decode_fixed::<32>(&receipt.issuer.public_key)?);
    let verification_key = if let Some(entry) = trusted_issuer_entry {
        Ed25519PublicKey(decode_fixed::<32>(&entry.public_key)?)
    } else if let Some(value) = pinned_public_key {
        Ed25519PublicKey(decode_fixed::<32>(value)?)
    } else {
        embedded_key
    };
    let trusted_issuer = trusted_issuer_entry.is_some() || pinned_public_key.is_some();
    let signature_valid = payload_hash_valid
        && receipt.signing.algorithm == "Ed25519"
        && verify_ed25519_message_hash_bytes(
            &digest.0,
            &decode_fixed::<64>(&receipt.signing.signature)?,
            &verification_key.0,
        )
        .unwrap_or(false);

    let kernel_receipt = project_v2_receipt_to_kernel(&receipt, &payload)?;
    let kernel_report =
        ink_verify::verify_receipt(&kernel_receipt, &[], VerificationPolicy::default())
            .map_err(|err| ReceiptV2Error::Trust(format!("kernel verification failed: {err:?}")))?;
    let kernel_projection_valid = kernel_report.core.valid;

    let manifest = manifest_json
        .map(serde_json::from_slice::<ManifestJson>)
        .transpose()?;
    let mut scope = "receipt-only".to_string();
    let mut manifest_hash_valid = true;
    let mut evidence_summary_valid = true;
    let mut controls_summary_valid = true;

    if let Some(manifest) = manifest.as_ref() {
        if manifest.schema != MANIFEST_SCHEMA_V2 {
            return Err(ReceiptV2Error::InvalidInput(format!(
                "expected {}",
                MANIFEST_SCHEMA_V2
            )));
        }
        scope = "full-evidence".to_string();
        manifest_hash_valid = hash_manifest(manifest)? == parse_digest(&receipt.manifest_hash)?;
        evidence_summary_valid =
            hash_evidence_summary(manifest)? == parse_digest(&receipt.evidence_summary_hash)?;
    }

    if let Some(controls_json) = controls_json {
        let controls = normalize_controls(std::str::from_utf8(controls_json).map_err(|_| {
            ReceiptV2Error::InvalidInput("controls JSON must be valid utf-8".to_string())
        })?)?;
        controls_summary_valid =
            hash_controls_summary(&controls) == parse_digest(&receipt.controls_summary_hash)?;
    }

    let revocation = match revocation_list {
        Some(list) => verify_revocations(list, trust_registry, pinned_public_key, &receipt)?,
        None => RevocationOutcome {
            checked: false,
            ok: true,
            code: "ISSUER_KEY_REVOCATION_NOT_PERFORMED",
        },
    };

    let mut checks = Vec::new();
    checks.push(binary_check(
        "payload.hash",
        payload_hash_valid,
        "RECEIPT_PAYLOAD_HASH_MATCH",
        "PAYLOAD_DIGEST_MISMATCH",
    ));
    checks.push(binary_check(
        "receipt.signature",
        signature_valid,
        "RECEIPT_SIGNATURE_VALID",
        "INVALID_SIGNATURE",
    ));
    checks.push(binary_check(
        "issuer.trust",
        trusted_issuer,
        "ISSUER_KEY_TRUSTED",
        "UNTRUSTED_ISSUER",
    ));
    checks.push(if revocation.checked {
        binary_check(
            "issuer.revocation",
            revocation.ok,
            "ISSUER_KEY_NOT_REVOKED",
            revocation.code,
        )
    } else {
        VerificationCheck {
            id: "issuer.revocation".to_string(),
            status: "not_performed".to_string(),
            reason_code: revocation.code.to_string(),
        }
    });
    checks.push(binary_check(
        "kernel.projection",
        kernel_projection_valid,
        "KERNEL_PROJECTION_VALID",
        "KERNEL_PROJECTION_INVALID",
    ));

    if manifest.is_some() {
        checks.push(binary_check(
            "manifest.hash",
            manifest_hash_valid,
            "MANIFEST_HASH_MATCH",
            "MANIFEST_HASH_MISMATCH",
        ));
        checks.push(binary_check(
            "evidence.summary",
            evidence_summary_valid,
            "EVIDENCE_SUMMARY_MATCH",
            "EVIDENCE_SUMMARY_MISMATCH",
        ));
    } else {
        checks.push(VerificationCheck {
            id: "manifest.hash".to_string(),
            status: "not_performed".to_string(),
            reason_code: "MANIFEST_NOT_SUPPLIED".to_string(),
        });
        checks.push(VerificationCheck {
            id: "evidence.summary".to_string(),
            status: "not_performed".to_string(),
            reason_code: "MANIFEST_NOT_SUPPLIED".to_string(),
        });
    }

    if controls_json.is_some() {
        checks.push(binary_check(
            "controls.summary",
            controls_summary_valid,
            "CONTROLS_SUMMARY_MATCH",
            "CONTROLS_SUMMARY_MISMATCH",
        ));
    } else {
        checks.push(VerificationCheck {
            id: "controls.summary".to_string(),
            status: "not_performed".to_string(),
            reason_code: "CONTROLS_NOT_SUPPLIED".to_string(),
        });
    }

    let verify_only_encoding = receipt.signing.transcript_encoding != RECEIPT_ENCODING_TLV_V2
        && matches!(
            receipt.signing.transcript_encoding.as_str(),
            RECEIPT_ENCODING_TLV_V1_LEGACY | RECEIPT_ENCODING_JSON_CANONICAL_V1
        );

    if verify_only_encoding {
        checks.push(VerificationCheck {
            id: "policy.encoding".to_string(),
            status: if verify_policy.require_canonical_tlv_v2 {
                "fail".to_string()
            } else {
                "pass".to_string()
            },
            reason_code: if verify_policy.require_canonical_tlv_v2 {
                "VERIFY_ONLY_FORMAT_REJECTED".to_string()
            } else {
                "VERIFY_ONLY_FORMAT_ACCEPTED".to_string()
            },
        });
    }

    let mut code = "VALID_RECEIPT";
    if !payload_hash_valid {
        code = "PAYLOAD_DIGEST_MISMATCH";
    } else if !signature_valid {
        code = "INVALID_SIGNATURE";
    } else if !kernel_projection_valid {
        code = "KERNEL_PROJECTION_INVALID";
    } else if verify_policy.require_canonical_tlv_v2
        && receipt.signing.transcript_encoding != RECEIPT_ENCODING_TLV_V2
    {
        code = "VERIFY_ONLY_FORMAT_REJECTED";
    } else if verify_policy.require_trusted_issuer && !trusted_issuer {
        code = "UNTRUSTED_ISSUER";
    } else if verify_policy.require_revocation_check && !revocation.checked {
        code = "REVOCATION_CHECK_REQUIRED";
    } else if revocation.checked && !revocation.ok {
        code = revocation.code;
    } else if manifest.is_some()
        && verify_policy.require_manifest_hash_match_when_manifest_present
        && !manifest_hash_valid
    {
        code = "MANIFEST_HASH_MISMATCH";
    } else if manifest.is_some()
        && verify_policy.require_evidence_summary_match_when_manifest_present
        && !evidence_summary_valid
    {
        code = "EVIDENCE_SUMMARY_MISMATCH";
    } else if controls_json.is_some()
        && verify_policy.require_controls_summary_match_when_controls_present
        && !controls_summary_valid
    {
        code = "CONTROLS_SUMMARY_MISMATCH";
    }

    let policy_accepted = code == "VALID_RECEIPT";
    Ok(VerificationReportJson {
        schema: VERIFICATION_REPORT_SCHEMA_V1.to_string(),
        status: if policy_accepted {
            "valid".to_string()
        } else {
            "invalid".to_string()
        },
        code: code.to_string(),
        transcript_encoding: receipt.signing.transcript_encoding.clone(),
        receipt_profile: receipt.receipt_profile.clone(),
        issuer: receipt.issuer.name.clone(),
        key_id: receipt.signing.key_id.clone(),
        payload_digest_alg: receipt.signing.payload_hash.algorithm.clone(),
        payload_digest_hex: receipt.signing.payload_hash.digest.clone(),
        signature_valid,
        trusted_issuer,
        revocation_checked: revocation.checked,
        revocation_ok: revocation.ok,
        policy_accepted,
        verification_engine: "Rust ink-core".to_string(),
        network_required: false,
        scope,
        checks,
    })
}

fn verify_revocations(
    list: &RevocationListJson,
    trust_registry: Option<&TrustRegistryJson>,
    pinned_public_key: Option<&str>,
    receipt: &ReceiptJson,
) -> Result<RevocationOutcome> {
    let trusted_signer_entry = trust_registry.and_then(|registry| {
        registry
            .issuers
            .iter()
            .find(|entry| entry.key_id == list.signing.key_id && entry.status == "active")
    });

    let signer_key = if let Some(entry) = trusted_signer_entry {
        Ed25519PublicKey(decode_fixed::<32>(&entry.public_key)?)
    } else if let Some(value) = pinned_public_key {
        if list.signing.key_id == receipt.signing.key_id {
            Ed25519PublicKey(decode_fixed::<32>(value)?)
        } else {
            return Ok(RevocationOutcome {
                checked: true,
                ok: false,
                code: "UNTRUSTED_REVOCATION_LIST_SIGNER",
            });
        }
    } else if list.signing.key_id == receipt.signing.key_id {
        Ed25519PublicKey(decode_fixed::<32>(&receipt.issuer.public_key)?)
    } else {
        return Ok(RevocationOutcome {
            checked: true,
            ok: false,
            code: "UNTRUSTED_REVOCATION_LIST_SIGNER",
        });
    };

    let digest = revocation_list_digest(list)?;
    let expected_payload_hash = digest_json(&digest);
    if list.signing.payload_hash.algorithm != expected_payload_hash.algorithm
        || list.signing.payload_hash.digest != expected_payload_hash.digest
    {
        return Ok(RevocationOutcome {
            checked: true,
            ok: false,
            code: "REVOCATION_LIST_PAYLOAD_HASH_MISMATCH",
        });
    }
    if list.signing.algorithm != "Ed25519" {
        return Ok(RevocationOutcome {
            checked: true,
            ok: false,
            code: "REVOCATION_LIST_UNSUPPORTED_SIGNATURE_ALGORITHM",
        });
    }
    let signature_valid = verify_ed25519_message_hash_bytes(
        &digest.0,
        &decode_fixed::<64>(&list.signing.signature)?,
        &signer_key.0,
    )
    .unwrap_or(false);
    if !signature_valid {
        return Ok(RevocationOutcome {
            checked: true,
            ok: false,
            code: "REVOCATION_LIST_INVALID_SIGNATURE",
        });
    }
    if list
        .revoked_keys
        .iter()
        .any(|entry| entry.key_id == receipt.signing.key_id)
    {
        return Ok(RevocationOutcome {
            checked: true,
            ok: false,
            code: "REVOKED_ISSUER_KEY",
        });
    }
    Ok(RevocationOutcome {
        checked: true,
        ok: true,
        code: "ISSUER_KEY_NOT_REVOKED",
    })
}

fn binary_check(id: &str, valid: bool, pass_code: &str, fail_code: &str) -> VerificationCheck {
    VerificationCheck {
        id: id.to_string(),
        status: if valid {
            "pass".to_string()
        } else {
            "fail".to_string()
        },
        reason_code: if valid {
            pass_code.to_string()
        } else {
            fail_code.to_string()
        },
    }
}

fn normalize_model(json_model: &ModelWaistJson) -> Result<ModelWaist<'static>> {
    if json_model.schema != "ink.model-waist.v1" {
        return Err(ReceiptV2Error::InvalidInput(
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

fn normalize_controls(raw: &str) -> Result<Vec<ControlObservation>> {
    let controls: ControlsFile = serde_json::from_str(raw)?;
    if controls.schema != CONTROLS_SCHEMA_V1 {
        return Err(ReceiptV2Error::InvalidInput(format!(
            "expected {}",
            CONTROLS_SCHEMA_V1
        )));
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

fn receipt_payload_from_json(receipt: &ReceiptJson) -> Result<ReceiptPayload<'static>> {
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
        return Err(ReceiptV2Error::InvalidInput(
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

fn project_v2_receipt_to_kernel(
    receipt: &ReceiptJson,
    payload: &ReceiptPayload<'_>,
) -> Result<ReceiptEnvelope> {
    let schema_id = SchemaId::from_str(RECEIPT_SCHEMA_V2)?;
    let schema_authority = SchemaAuthority::from_str("ink-host")?;
    let domain_tag = DomainTag::from_str("compat-v2")?;
    let issuer_id = kernel_projection_issuer_id(&receipt.issuer.key_id)?;
    let sequence = u64::try_from(receipt.issued_at).map_err(|_| {
        ReceiptV2Error::InvalidInput("receipt issued_at must be non-negative".to_string())
    })?;
    let claim_hash = kernel_projection_claim_hash(receipt, payload)?;
    let trace_hash = to_kernel_digest(receipt_transcript_hash(payload)?);

    ReceiptEnvelope::create(
        schema_id,
        to_kernel_digest(sha256(RECEIPT_SCHEMA_V2.as_bytes())),
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
    )
    .seal()
    .map_err(ReceiptV2Error::from)
}

fn kernel_projection_issuer_id(key_id: &str) -> Result<IssuerId> {
    let key_hash = sha256(key_id.as_bytes());
    let compact = format!("issuer:{}", hex::encode(&key_hash.0[..16]));
    IssuerId::from_str(&compact).map_err(ReceiptV2Error::from)
}

fn kernel_projection_claim_hash(
    receipt: &ReceiptJson,
    payload: &ReceiptPayload<'_>,
) -> Result<KernelDigest> {
    let mut parts = Vec::with_capacity(4 + receipt.reason_codes.len());
    parts.push(payload.action_id.as_bytes());
    parts.push(receipt.decision.as_bytes());
    parts.push(receipt.facts.risk_class.as_bytes());
    parts.push(receipt.policy.id.as_bytes());
    for reason in &receipt.reason_codes {
        parts.push(reason.as_bytes());
    }
    ink_core::hash::hash_many_labeled(b"compat-v2.claim", &parts).map_err(ReceiptV2Error::from)
}

fn revocation_list_digest(list: &RevocationListJson) -> Result<Sha256Digest> {
    let mut value = serde_json::to_value(list)?;
    if let Some(map) = value.as_object_mut() {
        map.remove("signing");
    }
    Ok(sha256(&canonicalize_legacy(&value)))
}

fn receipt_digest_for_encoding(
    receipt: &ReceiptJson,
    payload: &ReceiptPayload<'_>,
    encoding: &str,
) -> Result<Sha256Digest> {
    match encoding {
        RECEIPT_ENCODING_TLV_V2 => receipt_transcript_hash(payload).map_err(ReceiptV2Error::from),
        RECEIPT_ENCODING_TLV_V1_LEGACY => {
            receipt_transcript_hash_legacy_v1(payload).map_err(ReceiptV2Error::from)
        }
        RECEIPT_ENCODING_JSON_CANONICAL_V1 => {
            let mut value = serde_json::to_value(receipt)?;
            if let Some(map) = value.as_object_mut() {
                map.remove("signing");
            }
            Ok(sha256(&canonicalize_legacy(&value)))
        }
        other => Err(ReceiptV2Error::InvalidInput(format!(
            "unsupported receipt transcript encoding {other}"
        ))),
    }
}

fn hash_manifest(manifest: &ManifestJson) -> Result<Sha256Digest> {
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
        .collect::<Result<Vec<_>>>()?;
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

fn hash_evidence_summary(manifest: &ManifestJson) -> Result<Sha256Digest> {
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

fn parse_digest(value: &DigestJson) -> Result<Sha256Digest> {
    parse_hex_digest(&value.digest)
}

fn to_kernel_digest(value: Sha256Digest) -> KernelDigest {
    KernelDigest(value.0)
}

fn parse_hex_digest(value: &str) -> Result<Sha256Digest> {
    let bytes = hex::decode(value)
        .map_err(|_| ReceiptV2Error::InvalidInput(format!("invalid digest {value}")))?;
    let array: [u8; 32] = bytes
        .try_into()
        .map_err(|_| ReceiptV2Error::InvalidInput(format!("invalid digest {value}")))?;
    Ok(Sha256Digest(array))
}

fn decode_fixed<const N: usize>(value: &str) -> Result<[u8; N]> {
    let bytes = Base64UrlUnpadded::decode_vec(value)
        .map_err(|_| ReceiptV2Error::InvalidInput("invalid base64".to_string()))?;
    bytes
        .try_into()
        .map_err(|_| ReceiptV2Error::InvalidInput("invalid fixed length".to_string()))
}

fn leak_bounded<const N: usize>(value: String) -> Result<BoundedBytes<'static, N>> {
    let leaked = Box::leak(value.into_boxed_str());
    BoundedBytes::new(leaked.as_bytes()).map_err(ReceiptV2Error::from)
}

fn leak_action_id(value: String) -> Result<ActionId<'static>> {
    let leaked = Box::leak(value.into_boxed_str());
    BoundedBytes::new_identifier(leaked.as_bytes()).map_err(ReceiptV2Error::from)
}

fn leak_receipt_id(value: String) -> Result<ReceiptId<'static>> {
    let leaked = Box::leak(value.into_boxed_str());
    BoundedBytes::new_identifier(leaked.as_bytes()).map_err(ReceiptV2Error::from)
}

fn leak_key_id(value: String) -> Result<KeyId<'static>> {
    let leaked = Box::leak(value.into_boxed_str());
    BoundedBytes::new_identifier(leaked.as_bytes()).map_err(ReceiptV2Error::from)
}

fn digest_json(value: &Sha256Digest) -> DigestJson {
    DigestJson {
        algorithm: "sha-256".to_string(),
        digest: hex::encode(value.0),
    }
}

fn policy_decision_from_public(value: &str) -> ink_core::legacy::policy::Decision {
    match value {
        "pass" => ink_core::legacy::policy::Decision::Pass,
        "warn" => ink_core::legacy::policy::Decision::Warn,
        _ => ink_core::legacy::policy::Decision::Block,
    }
}

fn risk_class_from_str(value: &str) -> Result<RiskClass> {
    match value {
        "low" => Ok(RiskClass::Low),
        "medium" => Ok(RiskClass::Medium),
        "high" | "critical" => Ok(RiskClass::High),
        _ => Err(ReceiptV2Error::InvalidInput(format!(
            "unknown risk class {value}"
        ))),
    }
}

fn control_type_from_str(value: &str) -> Result<ControlType> {
    match value {
        "human_review" => Ok(ControlType::HumanReview),
        "approval" => Ok(ControlType::Approval),
        "dual_control" => Ok(ControlType::DualControl),
        "policy_exception" => Ok(ControlType::PolicyException),
        "supervisor_override" => Ok(ControlType::SupervisorOverride),
        "external_audit" => Ok(ControlType::ExternalAudit),
        _ => Err(ReceiptV2Error::InvalidInput(format!(
            "unknown control type {value}"
        ))),
    }
}

fn control_status_from_str(value: &str) -> Result<ControlStatus> {
    match value {
        "present" => Ok(ControlStatus::Present),
        "approved" => Ok(ControlStatus::Approved),
        "rejected" => Ok(ControlStatus::Rejected),
        "expired" => Ok(ControlStatus::Expired),
        "invalid" => Ok(ControlStatus::Invalid),
        _ => Err(ReceiptV2Error::InvalidInput(format!(
            "unknown control status {value}"
        ))),
    }
}

fn model_class_from_str(value: &str) -> Result<ModelClass> {
    match value {
        "open_weight" => Ok(ModelClass::OpenWeight),
        "closed_weight" => Ok(ModelClass::ClosedWeight),
        "hosted_api" => Ok(ModelClass::HostedApi),
        "replay" => Ok(ModelClass::Replay),
        "deterministic_demo" => Ok(ModelClass::DeterministicDemo),
        _ => Err(ReceiptV2Error::InvalidInput(format!(
            "unknown model class {value}"
        ))),
    }
}

fn runtime_kind_from_str(value: &str) -> Result<RuntimeKind> {
    match value {
        "deterministic_demo" => Ok(RuntimeKind::DeterministicDemo),
        "local_open_weight_model" => Ok(RuntimeKind::LocalOpenWeightModel),
        "local_closed_weight_model" => Ok(RuntimeKind::LocalClosedWeightModel),
        "hosted_model_api" => Ok(RuntimeKind::HostedModelApi),
        "hosted_model_gateway" => Ok(RuntimeKind::HostedModelGateway),
        "external_process" => Ok(RuntimeKind::ExternalProcess),
        "replay_only" => Ok(RuntimeKind::ReplayOnly),
        _ => Err(ReceiptV2Error::InvalidInput(format!(
            "unknown runtime kind {value}"
        ))),
    }
}

fn execution_topology_from_str(value: &str) -> Result<ExecutionTopology> {
    match value {
        "rule_based_local" => Ok(ExecutionTopology::RuleBasedLocal),
        "local_process" => Ok(ExecutionTopology::LocalProcess),
        "local_container" => Ok(ExecutionTopology::LocalContainer),
        "remote_provider" => Ok(ExecutionTopology::RemoteProvider),
        "remote_gateway" => Ok(ExecutionTopology::RemoteGateway),
        "external_subprocess" => Ok(ExecutionTopology::ExternalSubprocess),
        "replay_file" => Ok(ExecutionTopology::ReplayFile),
        _ => Err(ReceiptV2Error::InvalidInput(format!(
            "unknown execution topology {value}"
        ))),
    }
}

fn replay_strength_from_str(value: &str) -> Result<ReplayStrength> {
    match value {
        "fully_replayable" => Ok(ReplayStrength::FullyReplayable),
        "input_weights_config_bound" => Ok(ReplayStrength::InputWeightsConfigBound),
        "request_response_bound" => Ok(ReplayStrength::RequestResponseBound),
        "declared_only" => Ok(ReplayStrength::DeclaredOnly),
        "not_replayable" => Ok(ReplayStrength::NotReplayable),
        _ => Err(ReceiptV2Error::InvalidInput(format!(
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

fn plugin_trust_fact_from_str(value: &str) -> Result<PluginTrustFact> {
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

fn artifact_type_from_str(value: &str) -> Result<ArtifactType> {
    match value {
        "action_json" => Ok(ArtifactType::ActionProposal),
        "prompt_text" => Ok(ArtifactType::Prompt),
        "controls_json" => Ok(ArtifactType::ControlSet),
        "policy_json" => Ok(ArtifactType::PolicySpec),
        "policy_compilation_json" => Ok(ArtifactType::PolicyCompilation),
        _ => Ok(ArtifactType::Other),
    }
}

fn media_type_from_str(value: &str) -> Result<MediaType> {
    match value {
        "application/json" => Ok(MediaType::ApplicationJson),
        "text/plain; charset=utf-8" => Ok(MediaType::TextPlain),
        "application/yaml" => Ok(MediaType::ApplicationYaml),
        "application/octet-stream" => Ok(MediaType::ApplicationOctetStream),
        _ => Err(ReceiptV2Error::InvalidInput(format!(
            "unknown media type {value}"
        ))),
    }
}

#[cfg(test)]
mod tests {
    use super::{verify_receipt, VerificationReportJson};
    use serde::Deserialize;
    use serde_json::Value;
    use std::path::Path;

    #[derive(Debug, Deserialize)]
    struct VectorFile {
        vectors: Vec<SharedVector>,
    }

    #[derive(Debug, Deserialize)]
    struct SharedVector {
        name: String,
        receipt: Value,
        manifest: Option<Value>,
        trust_registry: Option<Value>,
        verify_policy: Option<Value>,
        pinned_public_key: Option<String>,
        expect_status: String,
        expect_code: String,
    }

    fn load_vectors() -> VectorFile {
        let path =
            Path::new(env!("CARGO_MANIFEST_DIR")).join("../../../test-vectors/ink-vectors.json");
        serde_json::from_slice(&std::fs::read(path).unwrap()).unwrap()
    }

    fn run_vector(vector: &SharedVector) -> VerificationReportJson {
        verify_receipt(
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
        .unwrap_or_else(|err| panic!("vector {} failed: {err}", vector.name))
    }

    #[test]
    fn shared_vectors_verify_with_expected_status_and_code() {
        let vectors = load_vectors();
        for vector in &vectors.vectors {
            let report = run_vector(vector);
            assert_eq!(
                report.status, vector.expect_status,
                "vector {}",
                vector.name
            );
            assert_eq!(report.code, vector.expect_code, "vector {}", vector.name);
        }
    }
}
