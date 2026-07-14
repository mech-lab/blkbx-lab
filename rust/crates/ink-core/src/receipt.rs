use crate::digest::{
    write_bool_field, write_i64_field, write_tlv, write_u32_field, write_u8_field, Sha256Sink,
    TranscriptSink,
};
use crate::domain::{FACTS_DOMAIN, MODEL_WAIST_DOMAIN, RECEIPT_TRANSCRIPT_DOMAIN, RUNTIME_DOMAIN};
use crate::error::Error;
use crate::limits::{
    MAX_ISSUER_NAME_LEN, MAX_POLICY_ID_LEN, MAX_POLICY_VERSION_LEN, MAX_REASONS,
    MAX_REASON_CODE_LEN,
};
use crate::model_waist::{
    DataCollectionPolicy, IdentityEvidence, ModelWaist, PluginApiVersion, PluginClaim,
    PluginTrustLevel, RequestedOutput, RuntimeClaim,
};
use crate::policy::{Decision, EvaluationOut, PluginTrustFact, PolicyFacts, ReasonCodeSlot};
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

fn write_digest_field(sink: &mut impl TranscriptSink, field_id: u16, digest: Sha256Digest) {
    write_tlv(sink, field_id, &digest.0);
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
    write_tlv(&mut sink, 1, RUNTIME_DOMAIN);
    write_u8_field(&mut sink, 2, runtime.runtime_kind as u8);
    write_u8_field(&mut sink, 3, runtime.execution_topology as u8);
    write_u8_field(&mut sink, 4, runtime.replay_strength as u8);
    write_bool_field(&mut sink, 5, runtime.determinism.deterministic);
    write_bool_field(&mut sink, 6, runtime.determinism.seed_bound);
    write_bool_field(&mut sink, 7, runtime.isolation.process_isolated);
    write_bool_field(&mut sink, 8, runtime.provider_routing.fallbacks_allowed);
    write_bool_field(&mut sink, 9, runtime.provider_routing.provider_pinned);
    write_u8_field(
        &mut sink,
        10,
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
    write_digest_field(&mut sink, 1, plugin.plugin_id_hash);
    write_digest_field(&mut sink, 2, plugin.plugin_version_hash);
    write_u8_field(
        &mut sink,
        3,
        match plugin.plugin_api_version {
            PluginApiVersion::V1 => 1,
        },
    );
    write_u8_field(&mut sink, 4, plugin.maintainer_class as u8);
    write_bool_field(&mut sink, 5, plugin.normalization.input_normalized);
    write_bool_field(&mut sink, 6, plugin.normalization.output_normalized);
    write_bool_field(&mut sink, 7, plugin.normalization.raw_request_preserved);
    write_bool_field(&mut sink, 8, plugin.normalization.raw_response_preserved);
    write_bool_field(&mut sink, 9, plugin.normalization.secrets_redacted);
    write_digest_field(&mut sink, 10, plugin.plugin_manifest_hash);
    write_tlv(&mut sink, 11, plugin.plugin_id_hint.as_bytes());
    write_u8_field(&mut sink, 12, plugin.trust_level as u8);
    sink.finalize()
}

pub fn policy_facts_hash(facts: PolicyFacts) -> Sha256Digest {
    let mut sink = Sha256Sink::new();
    write_tlv(&mut sink, 1, FACTS_DOMAIN);
    write_u8_field(&mut sink, 2, facts.risk_class as u8);
    write_bool_field(&mut sink, 3, facts.requires_human_review);
    write_bool_field(&mut sink, 4, facts.binding_effect_present);
    write_bool_field(&mut sink, 5, facts.provider_fallbacks_allowed);
    write_u8_field(&mut sink, 6, facts.plugin_trust_level as u8);
    write_u8_field(&mut sink, 7, facts.runtime_kind as u8);
    write_u8_field(&mut sink, 8, facts.replay_strength as u8);
    write_u8_field(&mut sink, 9, facts.model_class as u8);
    sink.finalize()
}

pub fn model_waist_hash(model: ModelWaist<'_>) -> Result<Sha256Digest, Error> {
    model.validate()?;
    let mut sink = Sha256Sink::new();
    write_tlv(&mut sink, 1, MODEL_WAIST_DOMAIN);
    write_u8_field(&mut sink, 2, model.identity.model_class as u8);
    write_digest_field(&mut sink, 3, model.identity.model_ref_hash);
    write_tlv(&mut sink, 4, model.identity.model_slug.as_bytes());
    match model.identity.identity_evidence {
        IdentityEvidence::Declared => write_u8_field(&mut sink, 5, 1),
        IdentityEvidence::ProviderDeclared {
            provider_model_id_hash,
        } => {
            write_u8_field(&mut sink, 5, 2);
            write_digest_field(&mut sink, 6, provider_model_id_hash);
        }
        IdentityEvidence::LocalFilesHashed {
            weights_hash,
            tokenizer_hash,
            config_hash,
        } => {
            write_u8_field(&mut sink, 5, 3);
            write_digest_field(&mut sink, 6, weights_hash);
            write_optional_digest_field(&mut sink, 7, tokenizer_hash)?;
            write_optional_digest_field(&mut sink, 8, config_hash)?;
        }
        IdentityEvidence::ContainerHashed { image_hash } => {
            write_u8_field(&mut sink, 5, 4);
            write_digest_field(&mut sink, 6, image_hash);
        }
    }
    write_digest_field(&mut sink, 9, model.invocation.action_hash);
    write_digest_field(&mut sink, 10, model.invocation.messages_hash);
    write_optional_digest_field(&mut sink, 11, model.invocation.system_prompt_hash)?;
    write_optional_digest_field(&mut sink, 12, model.invocation.tool_spec_hash)?;
    write_optional_digest_field(&mut sink, 13, model.invocation.response_schema_hash)?;
    write_digest_field(&mut sink, 14, model.invocation.parameters_hash);
    match model.invocation.requested_output {
        RequestedOutput::FreeText => write_u8_field(&mut sink, 15, 1),
        RequestedOutput::JsonSchema { schema_hash } => {
            write_u8_field(&mut sink, 15, 2);
            write_digest_field(&mut sink, 16, schema_hash);
        }
        RequestedOutput::ToolCall { tool_spec_hash } => {
            write_u8_field(&mut sink, 15, 3);
            write_digest_field(&mut sink, 16, tool_spec_hash);
        }
    }
    write_optional_digest_field(&mut sink, 17, model.observation.output_text_hash)?;
    write_optional_digest_field(&mut sink, 18, model.observation.structured_output_hash)?;
    write_optional_digest_field(&mut sink, 19, model.observation.provider_metadata_hash)?;
    write_u8_field(&mut sink, 20, model.observation.finish_reason as u8);
    write_u32_field(
        &mut sink,
        21,
        model.observation.usage.input_tokens.unwrap_or(0),
    );
    write_u32_field(
        &mut sink,
        22,
        model.observation.usage.output_tokens.unwrap_or(0),
    );
    write_u32_field(
        &mut sink,
        23,
        model.observation.usage.total_tokens.unwrap_or(0),
    );
    write_digest_field(&mut sink, 24, runtime_claim_hash(model.runtime));
    write_digest_field(&mut sink, 25, hash_plugin(model.plugin));
    Ok(sink.finalize())
}

pub fn write_receipt_transcript(
    payload: &ReceiptPayload<'_>,
    sink: &mut impl TranscriptSink,
) -> Result<(), Error> {
    payload.validate()?;
    write_tlv(sink, 1, RECEIPT_TRANSCRIPT_DOMAIN);
    write_u8_field(sink, 2, payload.schema_version.as_u8());
    write_tlv(sink, 3, payload.receipt_id.as_bytes());
    write_u8_field(sink, 4, payload.receipt_profile.as_u8());
    write_tlv(sink, 5, payload.action_id.as_bytes());
    write_i64_field(sink, 6, payload.issued_at.unix_seconds);
    write_u32_field(sink, 7, payload.issued_at.nanos);
    write_tlv(sink, 8, payload.issuer.name.as_bytes());
    write_tlv(sink, 9, payload.issuer.key_id.as_bytes());
    write_tlv(sink, 10, &payload.issuer.public_key.0);
    write_digest_field(sink, 11, payload.manifest_hash);
    write_tlv(sink, 12, payload.policy.policy_id.as_bytes());
    write_tlv(sink, 13, payload.policy.policy_version.as_bytes());
    write_digest_field(sink, 14, payload.policy.policy_hash);
    write_digest_field(sink, 15, runtime_claim_hash(payload.model.runtime));
    write_digest_field(sink, 16, model_waist_hash(payload.model)?);
    write_digest_field(sink, 17, policy_facts_hash(payload.facts));
    write_u8_field(sink, 18, payload.decision.as_u8());
    for reason in payload.reasons {
        write_tlv(sink, 19, reason.bytes);
    }
    write_digest_field(sink, 20, payload.evidence_summary_hash);
    write_digest_field(sink, 21, payload.controls_summary_hash);
    Ok(())
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
