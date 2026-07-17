use super::policy::{Decision, EvaluationOut, PluginTrustFact, PolicyFacts, ReasonCodeSlot};
use crate::digest::{
    write_bool_field, write_i64_field, write_tlv, write_u32_field, write_u8_field, Sha256Sink,
    TranscriptSink,
};
use crate::domain::{
    FACTS_DOMAIN, MODEL_WAIST_DOMAIN, RECEIPT_TRANSCRIPT_LEGACY_V1_DOMAIN,
    RECEIPT_TRANSCRIPT_TLV_V2_DOMAIN, RUNTIME_DOMAIN,
};
use crate::error::Error;
use crate::field_ids;
use crate::limits::{
    MAX_ISSUER_NAME_LEN, MAX_POLICY_ID_LEN, MAX_POLICY_VERSION_LEN, MAX_REASONS,
    MAX_REASON_CODE_LEN,
};
use crate::model_waist::{
    DataCollectionPolicy, IdentityEvidence, ModelWaist, PluginApiVersion, PluginClaim,
    PluginTrustLevel, RequestedOutput, RuntimeClaim,
};
use crate::types::{
    ActionId, BoundedBytes, Ed25519PublicKey, KeyId, ReceiptId, Sha256Digest, TimestampUtc,
};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ReceiptSchemaVersion {
    V2,
}

impl ReceiptSchemaVersion {
    pub fn as_u8(self) -> u8 {
        2
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ReceiptProfile {
    ThinWaistV2,
}

impl ReceiptProfile {
    pub fn as_u8(self) -> u8 {
        1
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct IssuerClaim<'a> {
    pub name: BoundedBytes<'a, MAX_ISSUER_NAME_LEN>,
    pub key_id: KeyId<'a>,
    pub public_key: Ed25519PublicKey,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PolicyBinding<'a> {
    pub policy_id: BoundedBytes<'a, MAX_POLICY_ID_LEN>,
    pub policy_version: BoundedBytes<'a, MAX_POLICY_VERSION_LEN>,
    pub policy_hash: Sha256Digest,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ReceiptPayload<'a> {
    pub schema_version: ReceiptSchemaVersion,
    pub receipt_id: ReceiptId<'a>,
    pub receipt_profile: ReceiptProfile,
    pub action_id: ActionId<'a>,
    pub issued_at: TimestampUtc,
    pub issuer: IssuerClaim<'a>,
    pub manifest_hash: Sha256Digest,
    pub policy: PolicyBinding<'a>,
    pub model: ModelWaist<'a>,
    pub facts: PolicyFacts,
    pub decision: Decision,
    pub reasons: &'a [ReasonCodeSlot<'a>],
    pub evidence_summary_hash: Sha256Digest,
    pub controls_summary_hash: Sha256Digest,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ReceiptInput<'a> {
    pub receipt_id: ReceiptId<'a>,
    pub action_id: ActionId<'a>,
    pub issued_at: TimestampUtc,
    pub issuer: IssuerClaim<'a>,
    pub manifest_hash: Sha256Digest,
    pub policy: PolicyBinding<'a>,
    pub model: ModelWaist<'a>,
    pub facts: PolicyFacts,
    pub evidence_summary_hash: Sha256Digest,
    pub controls_summary_hash: Sha256Digest,
}

impl<'a> ReceiptInput<'a> {
    pub fn validate(&self) -> Result<(), Error> {
        self.issued_at.validate()?;
        self.model.validate()?;
        if self.facts.runtime_kind != self.model.runtime.runtime_kind
            || self.facts.replay_strength != self.model.runtime.replay_strength
            || self.facts.model_class != self.model.identity.model_class
            || self.facts.plugin_trust_level != plugin_trust_fact(self.model.plugin.trust_level)
        {
            return Err(Error::InconsistentReceiptPayload);
        }
        Ok(())
    }
}

impl<'a> ReceiptPayload<'a> {
    pub fn validate(&self) -> Result<(), Error> {
        ReceiptInput {
            receipt_id: self.receipt_id,
            action_id: self.action_id,
            issued_at: self.issued_at,
            issuer: self.issuer,
            manifest_hash: self.manifest_hash,
            policy: self.policy,
            model: self.model,
            facts: self.facts,
            evidence_summary_hash: self.evidence_summary_hash,
            controls_summary_hash: self.controls_summary_hash,
        }
        .validate()?;
        if self.reasons.is_empty() {
            return Err(Error::EmptyValue);
        }
        if self.reasons.len() > MAX_REASONS {
            return Err(Error::TooManyReasons);
        }
        for reason in self.reasons {
            BoundedBytes::<MAX_REASON_CODE_LEN>::new_reason_code(reason.bytes)?;
        }
        Ok(())
    }
}

pub fn build_receipt_payload<'a>(
    input: ReceiptInput<'a>,
    evaluation: &'a EvaluationOut<'a>,
) -> Result<ReceiptPayload<'a>, Error> {
    input.validate()?;
    let payload = ReceiptPayload {
        schema_version: ReceiptSchemaVersion::V2,
        receipt_id: input.receipt_id,
        receipt_profile: ReceiptProfile::ThinWaistV2,
        action_id: input.action_id,
        issued_at: input.issued_at,
        issuer: input.issuer,
        manifest_hash: input.manifest_hash,
        policy: input.policy,
        model: input.model,
        facts: input.facts,
        decision: evaluation.decision,
        reasons: evaluation.reasons.as_slice(),
        evidence_summary_hash: input.evidence_summary_hash,
        controls_summary_hash: input.controls_summary_hash,
    };
    payload.validate()?;
    Ok(payload)
}

fn write_digest_field(
    sink: &mut impl TranscriptSink,
    field_id: u16,
    digest: Sha256Digest,
) -> Result<(), Error> {
    write_tlv(sink, field_id, &digest.0)?;
    Ok(())
}

fn write_optional_digest_field(
    sink: &mut impl TranscriptSink,
    field_id: u16,
    digest: Option<Sha256Digest>,
) -> Result<(), Error> {
    match digest {
        Some(value) => write_digest_field(sink, field_id, value)?,
        None => write_tlv(sink, field_id, &[])?,
    }
    Ok(())
}

pub fn runtime_claim_hash(runtime: RuntimeClaim) -> Sha256Digest {
    let mut sink = Sha256Sink::new();
    let _ = write_tlv(&mut sink, field_ids::runtime_claim::DOMAIN, RUNTIME_DOMAIN);
    write_u8_field(
        &mut sink,
        field_ids::runtime_claim::RUNTIME_KIND,
        runtime.runtime_kind as u8,
    );
    write_u8_field(
        &mut sink,
        field_ids::runtime_claim::EXECUTION_TOPOLOGY,
        runtime.execution_topology as u8,
    );
    write_u8_field(
        &mut sink,
        field_ids::runtime_claim::REPLAY_STRENGTH,
        runtime.replay_strength as u8,
    );
    write_bool_field(
        &mut sink,
        field_ids::runtime_claim::DETERMINISTIC,
        runtime.determinism.deterministic,
    );
    write_bool_field(
        &mut sink,
        field_ids::runtime_claim::SEED_BOUND,
        runtime.determinism.seed_bound,
    );
    write_bool_field(
        &mut sink,
        field_ids::runtime_claim::PROCESS_ISOLATED,
        runtime.isolation.process_isolated,
    );
    write_bool_field(
        &mut sink,
        field_ids::runtime_claim::FALLBACKS_ALLOWED,
        runtime.provider_routing.fallbacks_allowed,
    );
    write_bool_field(
        &mut sink,
        field_ids::runtime_claim::PROVIDER_PINNED,
        runtime.provider_routing.provider_pinned,
    );
    write_u8_field(
        &mut sink,
        field_ids::runtime_claim::DATA_COLLECTION_POLICY,
        match runtime.provider_routing.data_collection_policy {
            DataCollectionPolicy::DeclaredAllow => 1,
            DataCollectionPolicy::DeclaredDeny => 2,
            DataCollectionPolicy::Unknown => 3,
        },
    );
    sink.finalize()
}

fn hash_plugin(plugin: PluginClaim<'_>) -> Sha256Digest {
    let mut sink = Sha256Sink::new();
    let _ = write_digest_field(
        &mut sink,
        field_ids::plugin_claim::PLUGIN_ID_HASH,
        plugin.plugin_id_hash,
    );
    let _ = write_digest_field(
        &mut sink,
        field_ids::plugin_claim::PLUGIN_VERSION_HASH,
        plugin.plugin_version_hash,
    );
    write_u8_field(
        &mut sink,
        field_ids::plugin_claim::PLUGIN_API_VERSION,
        match plugin.plugin_api_version {
            PluginApiVersion::V1 => 1,
        },
    );
    write_u8_field(
        &mut sink,
        field_ids::plugin_claim::MAINTAINER_CLASS,
        plugin.maintainer_class as u8,
    );
    write_bool_field(
        &mut sink,
        field_ids::plugin_claim::INPUT_NORMALIZED,
        plugin.normalization.input_normalized,
    );
    write_bool_field(
        &mut sink,
        field_ids::plugin_claim::OUTPUT_NORMALIZED,
        plugin.normalization.output_normalized,
    );
    write_bool_field(
        &mut sink,
        field_ids::plugin_claim::RAW_REQUEST_PRESERVED,
        plugin.normalization.raw_request_preserved,
    );
    write_bool_field(
        &mut sink,
        field_ids::plugin_claim::RAW_RESPONSE_PRESERVED,
        plugin.normalization.raw_response_preserved,
    );
    write_bool_field(
        &mut sink,
        field_ids::plugin_claim::SECRETS_REDACTED,
        plugin.normalization.secrets_redacted,
    );
    let _ = write_digest_field(
        &mut sink,
        field_ids::plugin_claim::PLUGIN_MANIFEST_HASH,
        plugin.plugin_manifest_hash,
    );
    let _ = write_tlv(
        &mut sink,
        field_ids::plugin_claim::PLUGIN_ID_HINT,
        plugin.plugin_id_hint.as_bytes(),
    );
    write_u8_field(
        &mut sink,
        field_ids::plugin_claim::TRUST_LEVEL,
        plugin.trust_level as u8,
    );
    sink.finalize()
}

pub fn policy_facts_hash(facts: PolicyFacts) -> Sha256Digest {
    let mut sink = Sha256Sink::new();
    let _ = write_tlv(&mut sink, field_ids::policy_facts::DOMAIN, FACTS_DOMAIN);
    write_u8_field(
        &mut sink,
        field_ids::policy_facts::RISK_CLASS,
        facts.risk_class as u8,
    );
    write_bool_field(
        &mut sink,
        field_ids::policy_facts::REQUIRES_HUMAN_REVIEW,
        facts.requires_human_review,
    );
    write_bool_field(
        &mut sink,
        field_ids::policy_facts::BINDING_EFFECT_PRESENT,
        facts.binding_effect_present,
    );
    write_bool_field(
        &mut sink,
        field_ids::policy_facts::PROVIDER_FALLBACKS_ALLOWED,
        facts.provider_fallbacks_allowed,
    );
    write_u8_field(
        &mut sink,
        field_ids::policy_facts::PLUGIN_TRUST_LEVEL,
        facts.plugin_trust_level as u8,
    );
    write_u8_field(
        &mut sink,
        field_ids::policy_facts::RUNTIME_KIND,
        facts.runtime_kind as u8,
    );
    write_u8_field(
        &mut sink,
        field_ids::policy_facts::REPLAY_STRENGTH,
        facts.replay_strength as u8,
    );
    write_u8_field(
        &mut sink,
        field_ids::policy_facts::MODEL_CLASS,
        facts.model_class as u8,
    );
    sink.finalize()
}

pub fn model_waist_hash(model: ModelWaist<'_>) -> Result<Sha256Digest, Error> {
    model.validate()?;
    let mut sink = Sha256Sink::new();
    let _ = write_tlv(
        &mut sink,
        field_ids::model_waist::DOMAIN,
        MODEL_WAIST_DOMAIN,
    );
    write_u8_field(
        &mut sink,
        field_ids::model_waist::MODEL_CLASS,
        model.identity.model_class as u8,
    );
    let _ = write_digest_field(
        &mut sink,
        field_ids::model_waist::MODEL_REF_HASH,
        model.identity.model_ref_hash,
    );
    let _ = write_tlv(
        &mut sink,
        field_ids::model_waist::MODEL_SLUG,
        model.identity.model_slug.as_bytes(),
    );
    match model.identity.identity_evidence {
        IdentityEvidence::Declared => {
            write_u8_field(&mut sink, field_ids::model_waist::IDENTITY_EVIDENCE_KIND, 1)
        }
        IdentityEvidence::ProviderDeclared {
            provider_model_id_hash,
        } => {
            write_u8_field(&mut sink, field_ids::model_waist::IDENTITY_EVIDENCE_KIND, 2);
            let _ = write_digest_field(
                &mut sink,
                field_ids::model_waist::IDENTITY_EVIDENCE_DIGEST_A,
                provider_model_id_hash,
            );
        }
        IdentityEvidence::LocalFilesHashed {
            weights_hash,
            tokenizer_hash,
            config_hash,
        } => {
            write_u8_field(&mut sink, field_ids::model_waist::IDENTITY_EVIDENCE_KIND, 3);
            write_digest_field(
                &mut sink,
                field_ids::model_waist::IDENTITY_EVIDENCE_DIGEST_A,
                weights_hash,
            )?;
            write_optional_digest_field(
                &mut sink,
                field_ids::model_waist::IDENTITY_EVIDENCE_DIGEST_B,
                tokenizer_hash,
            )?;
            write_optional_digest_field(
                &mut sink,
                field_ids::model_waist::IDENTITY_EVIDENCE_DIGEST_C,
                config_hash,
            )?;
        }
        IdentityEvidence::ContainerHashed { image_hash } => {
            write_u8_field(&mut sink, field_ids::model_waist::IDENTITY_EVIDENCE_KIND, 4);
            let _ = write_digest_field(
                &mut sink,
                field_ids::model_waist::IDENTITY_EVIDENCE_DIGEST_A,
                image_hash,
            );
        }
    }
    let _ = write_digest_field(
        &mut sink,
        field_ids::model_waist::ACTION_HASH,
        model.invocation.action_hash,
    );
    let _ = write_digest_field(
        &mut sink,
        field_ids::model_waist::MESSAGES_HASH,
        model.invocation.messages_hash,
    );
    write_optional_digest_field(
        &mut sink,
        field_ids::model_waist::SYSTEM_PROMPT_HASH,
        model.invocation.system_prompt_hash,
    )?;
    write_optional_digest_field(
        &mut sink,
        field_ids::model_waist::TOOL_SPEC_HASH,
        model.invocation.tool_spec_hash,
    )?;
    write_optional_digest_field(
        &mut sink,
        field_ids::model_waist::RESPONSE_SCHEMA_HASH,
        model.invocation.response_schema_hash,
    )?;
    let _ = write_digest_field(
        &mut sink,
        field_ids::model_waist::PARAMETERS_HASH,
        model.invocation.parameters_hash,
    );
    match model.invocation.requested_output {
        RequestedOutput::FreeText => {
            write_u8_field(&mut sink, field_ids::model_waist::REQUESTED_OUTPUT_KIND, 1)
        }
        RequestedOutput::JsonSchema { schema_hash } => {
            write_u8_field(&mut sink, field_ids::model_waist::REQUESTED_OUTPUT_KIND, 2);
            let _ = write_digest_field(
                &mut sink,
                field_ids::model_waist::REQUESTED_OUTPUT_DIGEST,
                schema_hash,
            );
        }
        RequestedOutput::ToolCall { tool_spec_hash } => {
            write_u8_field(&mut sink, field_ids::model_waist::REQUESTED_OUTPUT_KIND, 3);
            let _ = write_digest_field(
                &mut sink,
                field_ids::model_waist::REQUESTED_OUTPUT_DIGEST,
                tool_spec_hash,
            );
        }
    }
    write_optional_digest_field(
        &mut sink,
        field_ids::model_waist::OUTPUT_TEXT_HASH,
        model.observation.output_text_hash,
    )?;
    write_optional_digest_field(
        &mut sink,
        field_ids::model_waist::STRUCTURED_OUTPUT_HASH,
        model.observation.structured_output_hash,
    )?;
    write_optional_digest_field(
        &mut sink,
        field_ids::model_waist::PROVIDER_METADATA_HASH,
        model.observation.provider_metadata_hash,
    )?;
    write_u8_field(
        &mut sink,
        field_ids::model_waist::FINISH_REASON,
        model.observation.finish_reason as u8,
    );
    write_u32_field(
        &mut sink,
        field_ids::model_waist::INPUT_TOKENS,
        model.observation.usage.input_tokens.unwrap_or(0),
    );
    write_u32_field(
        &mut sink,
        field_ids::model_waist::OUTPUT_TOKENS,
        model.observation.usage.output_tokens.unwrap_or(0),
    );
    write_u32_field(
        &mut sink,
        field_ids::model_waist::TOTAL_TOKENS,
        model.observation.usage.total_tokens.unwrap_or(0),
    );
    let _ = write_digest_field(
        &mut sink,
        field_ids::model_waist::RUNTIME_HASH,
        runtime_claim_hash(model.runtime),
    );
    let _ = write_digest_field(
        &mut sink,
        field_ids::model_waist::PLUGIN_HASH,
        hash_plugin(model.plugin),
    );
    Ok(sink.finalize())
}

pub fn write_receipt_transcript_legacy_v1(
    payload: &ReceiptPayload<'_>,
    sink: &mut impl TranscriptSink,
) -> Result<(), Error> {
    payload.validate()?;
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_legacy_v1::DOMAIN,
        RECEIPT_TRANSCRIPT_LEGACY_V1_DOMAIN,
    );
    write_u8_field(
        sink,
        field_ids::receipt_tlv_legacy_v1::SCHEMA_VERSION,
        payload.schema_version.as_u8(),
    );
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_legacy_v1::RECEIPT_ID,
        payload.receipt_id.as_bytes(),
    );
    write_u8_field(
        sink,
        field_ids::receipt_tlv_legacy_v1::RECEIPT_PROFILE,
        payload.receipt_profile.as_u8(),
    );
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_legacy_v1::ACTION_ID,
        payload.action_id.as_bytes(),
    );
    write_i64_field(
        sink,
        field_ids::receipt_tlv_legacy_v1::ISSUED_AT_SECONDS,
        payload.issued_at.unix_seconds,
    );
    write_u32_field(
        sink,
        field_ids::receipt_tlv_legacy_v1::ISSUED_AT_NANOS,
        payload.issued_at.nanos,
    );
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_legacy_v1::ISSUER_NAME,
        payload.issuer.name.as_bytes(),
    );
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_legacy_v1::KEY_ID,
        payload.issuer.key_id.as_bytes(),
    );
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_legacy_v1::PUBLIC_KEY,
        &payload.issuer.public_key.0,
    );
    write_digest_field(
        sink,
        field_ids::receipt_tlv_legacy_v1::MANIFEST_HASH,
        payload.manifest_hash,
    )?;
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_legacy_v1::POLICY_ID,
        payload.policy.policy_id.as_bytes(),
    );
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_legacy_v1::POLICY_VERSION,
        payload.policy.policy_version.as_bytes(),
    );
    write_digest_field(
        sink,
        field_ids::receipt_tlv_legacy_v1::POLICY_HASH,
        payload.policy.policy_hash,
    )?;
    write_digest_field(
        sink,
        field_ids::receipt_tlv_legacy_v1::RUNTIME_HASH,
        runtime_claim_hash(payload.model.runtime),
    )?;
    write_digest_field(
        sink,
        field_ids::receipt_tlv_legacy_v1::MODEL_HASH,
        model_waist_hash(payload.model)?,
    )?;
    write_digest_field(
        sink,
        field_ids::receipt_tlv_legacy_v1::FACTS_HASH,
        policy_facts_hash(payload.facts),
    )?;
    write_u8_field(
        sink,
        field_ids::receipt_tlv_legacy_v1::DECISION,
        payload.decision.as_u8(),
    );
    for reason in payload.reasons {
        let _ = write_tlv(sink, field_ids::receipt_tlv_legacy_v1::REASON, reason.bytes);
    }
    write_digest_field(
        sink,
        field_ids::receipt_tlv_legacy_v1::EVIDENCE_SUMMARY_HASH,
        payload.evidence_summary_hash,
    )?;
    write_digest_field(
        sink,
        field_ids::receipt_tlv_legacy_v1::CONTROLS_SUMMARY_HASH,
        payload.controls_summary_hash,
    )?;
    Ok(())
}

pub fn write_receipt_transcript(
    payload: &ReceiptPayload<'_>,
    sink: &mut impl TranscriptSink,
) -> Result<(), Error> {
    payload.validate()?;
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_v2::DOMAIN,
        RECEIPT_TRANSCRIPT_TLV_V2_DOMAIN,
    );
    write_u8_field(
        sink,
        field_ids::receipt_tlv_v2::SCHEMA_VERSION,
        payload.schema_version.as_u8(),
    );
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_v2::RECEIPT_ID,
        payload.receipt_id.as_bytes(),
    );
    write_u8_field(
        sink,
        field_ids::receipt_tlv_v2::RECEIPT_PROFILE,
        payload.receipt_profile.as_u8(),
    );
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_v2::ACTION_ID,
        payload.action_id.as_bytes(),
    );
    write_i64_field(
        sink,
        field_ids::receipt_tlv_v2::ISSUED_AT_SECONDS,
        payload.issued_at.unix_seconds,
    );
    write_u32_field(
        sink,
        field_ids::receipt_tlv_v2::ISSUED_AT_NANOS,
        payload.issued_at.nanos,
    );
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_v2::ISSUER_NAME,
        payload.issuer.name.as_bytes(),
    );
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_v2::KEY_ID,
        payload.issuer.key_id.as_bytes(),
    );
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_v2::PUBLIC_KEY,
        &payload.issuer.public_key.0,
    );
    write_digest_field(
        sink,
        field_ids::receipt_tlv_v2::MANIFEST_HASH,
        payload.manifest_hash,
    )?;
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_v2::POLICY_ID,
        payload.policy.policy_id.as_bytes(),
    );
    let _ = write_tlv(
        sink,
        field_ids::receipt_tlv_v2::POLICY_VERSION,
        payload.policy.policy_version.as_bytes(),
    );
    write_digest_field(
        sink,
        field_ids::receipt_tlv_v2::POLICY_HASH,
        payload.policy.policy_hash,
    )?;
    write_digest_field(
        sink,
        field_ids::receipt_tlv_v2::RUNTIME_HASH,
        runtime_claim_hash(payload.model.runtime),
    )?;
    write_digest_field(
        sink,
        field_ids::receipt_tlv_v2::MODEL_HASH,
        model_waist_hash(payload.model)?,
    )?;
    write_digest_field(
        sink,
        field_ids::receipt_tlv_v2::FACTS_HASH,
        policy_facts_hash(payload.facts),
    )?;
    write_u8_field(
        sink,
        field_ids::receipt_tlv_v2::DECISION,
        payload.decision.as_u8(),
    );
    write_u8_field(
        sink,
        field_ids::receipt_tlv_v2::REASON_COUNT,
        payload.reasons.len() as u8,
    );
    for (index, reason) in payload.reasons.iter().enumerate() {
        let field_id = field_ids::receipt_tlv_v2::REASON_BASE + (index as u16);
        let _ = write_tlv(sink, field_id, reason.bytes);
    }
    write_digest_field(
        sink,
        field_ids::receipt_tlv_v2::EVIDENCE_SUMMARY_HASH,
        payload.evidence_summary_hash,
    )?;
    write_digest_field(
        sink,
        field_ids::receipt_tlv_v2::CONTROLS_SUMMARY_HASH,
        payload.controls_summary_hash,
    )?;
    Ok(())
}

pub fn receipt_transcript_hash_legacy_v1(
    payload: &ReceiptPayload<'_>,
) -> Result<Sha256Digest, Error> {
    let mut sink = Sha256Sink::new();
    write_receipt_transcript_legacy_v1(payload, &mut sink)?;
    Ok(sink.finalize())
}

pub fn receipt_transcript_hash(payload: &ReceiptPayload<'_>) -> Result<Sha256Digest, Error> {
    let mut sink = Sha256Sink::new();
    write_receipt_transcript(payload, &mut sink)?;
    Ok(sink.finalize())
}

fn plugin_trust_fact(level: PluginTrustLevel) -> PluginTrustFact {
    match level {
        PluginTrustLevel::Untrusted => PluginTrustFact::Untrusted,
        PluginTrustLevel::LocallyAllowed => PluginTrustFact::LocallyAllowed,
        PluginTrustLevel::FirstPartyReference => PluginTrustFact::FirstPartyReference,
        PluginTrustLevel::ThirdPartyTrusted => PluginTrustFact::ThirdPartyTrusted,
        PluginTrustLevel::ReproduciblyBuilt => PluginTrustFact::ReproduciblyBuilt,
    }
}
