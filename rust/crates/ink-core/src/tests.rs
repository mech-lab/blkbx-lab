extern crate alloc;

use core::convert::TryInto;

use ed25519_dalek::{Signer, SigningKey, Verifier};

use crate::model_waist::{
    DataCollectionPolicy, DeterminismClaim, ExecutionTopology, FinishReason, IdentityEvidence,
    IsolationClaim, MaintainerClass, ModelClass, ModelIdentityClaim, ModelInvocationClaim,
    ModelObservationClaim, ModelWaist, NormalizationClaim, PluginApiVersion, PluginClaim,
    PluginTrustLevel, ProviderRoutingClaim, ReplayStrength, RequestedOutput, RuntimeClaim,
    RuntimeKind, TokenUsage,
};
use crate::policy::{
    Decision, PluginTrustFact, PolicyFacts, ReasonCodeSlot, RiskClass,
};
use crate::receipt::{
    receipt_transcript_hash, receipt_transcript_hash_legacy_v1, write_receipt_transcript,
    IssuerClaim, PolicyBinding, ReceiptPayload, ReceiptProfile, ReceiptSchemaVersion,
};
use crate::signing::verify_receipt_signature;
use crate::types::{
    ActionId, BoundedBytes, Ed25519PublicKey, KeyId, ReceiptId, Sha256Digest, TimestampUtc,
};
use alloc::format;
use alloc::vec::Vec;

struct VecSink {
    bytes: Vec<u8>,
}

impl VecSink {
    fn new() -> Self {
        Self {
            bytes: Vec::new(),
        }
    }
}

impl crate::digest::TranscriptSink for VecSink {
    fn update(&mut self, bytes: &[u8]) {
        self.bytes.extend_from_slice(bytes);
    }
}

fn sample_payload<'a>(process_isolated: bool, reasons: &'a [ReasonCodeSlot<'a>]) -> ReceiptPayload<'a> {
    let payload = ReceiptPayload {
        schema_version: ReceiptSchemaVersion::V2,
        receipt_id: ReceiptId::new_identifier(b"urn:ink:receipt:test").unwrap(),
        receipt_profile: ReceiptProfile::ThinWaistV2,
        action_id: ActionId::new_identifier(b"urn:ink:action:test").unwrap(),
        issued_at: TimestampUtc::new(1_720_000_000, 123_000_000).unwrap(),
        issuer: IssuerClaim {
            name: BoundedBytes::new_identifier(b"blkbx_local_dev").unwrap(),
            key_id: KeyId::new_identifier(b"kid_local_demo").unwrap(),
            public_key: Ed25519PublicKey([7u8; 32]),
        },
        manifest_hash: Sha256Digest([1u8; 32]),
        policy: PolicyBinding {
            policy_id: BoundedBytes::new_identifier(b"demo_claims").unwrap(),
            policy_version: BoundedBytes::new_identifier(b"v1").unwrap(),
            policy_hash: Sha256Digest([2u8; 32]),
        },
        model: ModelWaist {
            identity: ModelIdentityClaim {
                model_class: ModelClass::DeterministicDemo,
                model_ref_hash: Sha256Digest([3u8; 32]),
                model_slug: BoundedBytes::new_identifier(b"qwen35_demo").unwrap(),
                identity_evidence: IdentityEvidence::Declared,
            },
            invocation: ModelInvocationClaim {
                action_hash: Sha256Digest([4u8; 32]),
                messages_hash: Sha256Digest([5u8; 32]),
                system_prompt_hash: None,
                tool_spec_hash: None,
                response_schema_hash: None,
                parameters_hash: Sha256Digest([6u8; 32]),
                requested_output: RequestedOutput::FreeText,
            },
            observation: ModelObservationClaim {
                output_text_hash: Some(Sha256Digest([8u8; 32])),
                structured_output_hash: None,
                provider_metadata_hash: Some(Sha256Digest([9u8; 32])),
                finish_reason: FinishReason::Stop,
                usage: TokenUsage {
                    input_tokens: Some(10),
                    output_tokens: Some(5),
                    total_tokens: Some(15),
                },
            },
            runtime: RuntimeClaim {
                runtime_kind: RuntimeKind::DeterministicDemo,
                execution_topology: ExecutionTopology::RuleBasedLocal,
                replay_strength: ReplayStrength::FullyReplayable,
                determinism: DeterminismClaim {
                    deterministic: true,
                    seed_bound: true,
                },
                isolation: IsolationClaim { process_isolated },
                provider_routing: ProviderRoutingClaim {
                    fallbacks_allowed: false,
                    provider_pinned: true,
                    data_collection_policy: DataCollectionPolicy::DeclaredDeny,
                },
            },
            plugin: PluginClaim {
                plugin_id_hash: Sha256Digest([10u8; 32]),
                plugin_version_hash: Sha256Digest([11u8; 32]),
                plugin_api_version: PluginApiVersion::V1,
                maintainer_class: MaintainerClass::FirstPartyReference,
                normalization: NormalizationClaim {
                    input_normalized: true,
                    output_normalized: true,
                    raw_request_preserved: true,
                    raw_response_preserved: true,
                    secrets_redacted: true,
                },
                plugin_manifest_hash: Sha256Digest([12u8; 32]),
                plugin_id_hint: BoundedBytes::new_identifier(b"qwen35").unwrap(),
                trust_level: PluginTrustLevel::FirstPartyReference,
            },
        },
        facts: PolicyFacts {
            risk_class: RiskClass::Low,
            requires_human_review: false,
            binding_effect_present: false,
            provider_fallbacks_allowed: false,
            plugin_trust_level: PluginTrustFact::FirstPartyReference,
            runtime_kind: RuntimeKind::DeterministicDemo,
            replay_strength: ReplayStrength::FullyReplayable,
            model_class: ModelClass::DeterministicDemo,
        },
        decision: Decision::Pass,
        reasons,
        evidence_summary_hash: Sha256Digest([13u8; 32]),
        controls_summary_hash: Sha256Digest([14u8; 32]),
    };
    payload.validate().unwrap();
    payload
}

fn parse_tlv_field_ids(bytes: &[u8]) -> Vec<u16> {
    let mut field_ids = Vec::new();
    let mut cursor = 0usize;
    while cursor < bytes.len() {
        let field_id = u16::from_be_bytes(bytes[cursor..cursor + 2].try_into().unwrap());
        let length = u32::from_be_bytes(bytes[cursor + 2..cursor + 6].try_into().unwrap()) as usize;
        field_ids.push(field_id);
        cursor += 6 + length;
    }
    field_ids
}

#[test]
fn transcript_hash_changes_when_isolation_changes() {
    let reasons = [ReasonCodeSlot { bytes: b"RUNTIME_DETERMINISTIC_DEMO" }];
    let isolated = sample_payload(true, &reasons);
    let shared = sample_payload(false, &reasons);
    assert_ne!(receipt_transcript_hash(&isolated).unwrap(), receipt_transcript_hash(&shared).unwrap());
}

#[test]
fn tlv_v2_transcript_uses_unique_field_ids_at_max_reason_count() {
    let reason_values: Vec<Vec<u8>> = (0..crate::limits::MAX_REASONS)
        .map(|index| format!("REASON_{index:02}").into_bytes())
        .collect();
    let reason_slots: Vec<ReasonCodeSlot<'_>> = reason_values
        .iter()
        .map(|reason: &Vec<u8>| ReasonCodeSlot {
            bytes: reason.as_slice(),
        })
        .collect();
    let payload = sample_payload(true, reason_slots.as_slice());
    let mut sink = VecSink::new();
    write_receipt_transcript(&payload, &mut sink).unwrap();
    let field_ids = parse_tlv_field_ids(&sink.bytes);
    let unique_count = {
        let mut sorted = field_ids.clone();
        sorted.sort_unstable();
        sorted.dedup();
        sorted.len()
    };
    assert_eq!(field_ids.len(), unique_count);
}

#[test]
fn legacy_v1_transcript_reuses_reason_field_id() {
    let reasons = [
        ReasonCodeSlot { bytes: b"FIRST_REASON" },
        ReasonCodeSlot { bytes: b"SECOND_REASON" },
    ];
    let payload = sample_payload(true, &reasons);
    let legacy = receipt_transcript_hash_legacy_v1(&payload).unwrap();
    let current = receipt_transcript_hash(&payload).unwrap();
    assert_ne!(legacy, current);
}

#[test]
fn signing_round_trip_uses_current_payload_hash() {
    let reasons = [ReasonCodeSlot { bytes: b"RUNTIME_DETERMINISTIC_DEMO" }];
    let payload = sample_payload(true, &reasons);
    let secret = [42u8; 32];
    let signing_key = SigningKey::from_bytes(&secret);
    let signature = signing_key.sign(&receipt_transcript_hash(&payload).unwrap().0);
    let verifying_key = signing_key.verifying_key();
    verifying_key
        .verify(&receipt_transcript_hash(&payload).unwrap().0, &signature)
        .unwrap();
    verify_receipt_signature(
        &payload,
        &crate::types::Ed25519Signature(signature.to_bytes()),
        &Ed25519PublicKey(verifying_key.to_bytes()),
    )
    .unwrap();
}
