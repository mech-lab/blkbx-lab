extern crate std;

use ed25519_dalek::SigningKey;

use crate::compare::{compare_receipts, ComparisonOut, VerifiedReceiptSummary};
use crate::controls::{ControlObservation, ControlSet, ControlStatus, ControlType};
use crate::digest::sha256;
use crate::error::Error;
use crate::limits::{MAX_ARTIFACTS, MAX_CONTROLS};
use crate::manifest::{ArtifactRef, ArtifactType, ManifestBinding, MediaType};
use crate::model_waist::{
    DataCollectionPolicy, DeterminismClaim, ExecutionTopology, FinishReason, IdentityEvidence,
    IsolationClaim, MaintainerClass, ModelClass, ModelIdentityClaim, ModelInvocationClaim,
    ModelObservationClaim, ModelWaist, NormalizationClaim, PluginApiVersion, PluginClaim,
    PluginTrustLevel, ProviderRoutingClaim, ReplayStrength, RequestedOutput, RuntimeClaim,
    RuntimeKind, TokenUsage,
};
use crate::policy::{
    evaluate_policy, CompiledPolicy, CompiledRule, ConditionNode, ConditionOp, ConditionValue,
    Decision, EvaluationOut, PluginTrustFact, PolicyFacts, PolicyInput, ReasonCodeSlot,
    ReasonWriter, RiskClass, RuleEffect,
};
use crate::receipt::{
    build_receipt_payload, model_waist_hash, policy_facts_hash, receipt_transcript_hash,
    runtime_claim_hash, IssuerClaim, PolicyBinding, ReceiptInput,
};
use crate::signing::sign_receipt_payload;
use crate::types::{BoundedBytes, Ed25519PublicKey, Sha256Digest, TimestampUtc};
use crate::verify::{verify_receipt, VerificationOut, VerificationReason};

fn text<const N: usize>(bytes: &'static [u8]) -> BoundedBytes<'static, N> {
    BoundedBytes::new(bytes).unwrap()
}

fn identifier<const N: usize>(bytes: &'static [u8]) -> BoundedBytes<'static, N> {
    BoundedBytes::new_identifier(bytes).unwrap()
}

fn reason(bytes: &'static [u8]) -> BoundedBytes<'static, 96> {
    BoundedBytes::new_reason_code(bytes).unwrap()
}

fn demo_facts() -> PolicyFacts {
    PolicyFacts {
        risk_class: RiskClass::High,
        requires_human_review: true,
        binding_effect_present: false,
        provider_fallbacks_allowed: false,
        plugin_trust_level: PluginTrustFact::FirstPartyReference,
        runtime_kind: RuntimeKind::DeterministicDemo,
        replay_strength: ReplayStrength::FullyReplayable,
        model_class: ModelClass::DeterministicDemo,
    }
}

fn demo_model() -> ModelWaist<'static> {
    ModelWaist {
        identity: ModelIdentityClaim {
            model_class: ModelClass::DeterministicDemo,
            model_ref_hash: sha256(b"model-ref"),
            model_slug: text(b"qwen35-demo"),
            identity_evidence: IdentityEvidence::Declared,
        },
        invocation: ModelInvocationClaim {
            action_hash: sha256(b"action"),
            messages_hash: sha256(b"messages"),
            system_prompt_hash: Some(sha256(b"system")),
            tool_spec_hash: None,
            response_schema_hash: Some(sha256(b"schema")),
            parameters_hash: sha256(b"params"),
            requested_output: RequestedOutput::JsonSchema {
                schema_hash: sha256(b"schema"),
            },
        },
        observation: ModelObservationClaim {
            output_text_hash: Some(sha256(b"output")),
            structured_output_hash: None,
            provider_metadata_hash: Some(sha256(b"provider-meta")),
            finish_reason: FinishReason::Stop,
            usage: TokenUsage {
                input_tokens: Some(12),
                output_tokens: Some(3),
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
            isolation: IsolationClaim {
                process_isolated: true,
            },
            provider_routing: ProviderRoutingClaim {
                fallbacks_allowed: false,
                provider_pinned: true,
                data_collection_policy: DataCollectionPolicy::DeclaredDeny,
            },
        },
        plugin: PluginClaim {
            plugin_id_hash: sha256(b"plugin-id"),
            plugin_version_hash: sha256(b"plugin-version"),
            plugin_api_version: PluginApiVersion::V1,
            maintainer_class: MaintainerClass::FirstPartyReference,
            normalization: NormalizationClaim {
                input_normalized: true,
                output_normalized: true,
                raw_request_preserved: true,
                raw_response_preserved: true,
                secrets_redacted: true,
            },
            plugin_manifest_hash: sha256(b"plugin-manifest"),
            plugin_id_hint: text(b"qwen35-demo"),
            trust_level: PluginTrustLevel::FirstPartyReference,
        },
    }
}

fn demo_policy_parts() -> ([ConditionNode; 4], [CompiledRule<'static>; 2]) {
    let nodes = [
        ConditionNode {
            op: ConditionOp::RequiresHumanReview,
            left: 0,
            right: 0,
            value: ConditionValue::Bool(true),
        },
        ConditionNode {
            op: ConditionOp::Not,
            left: 2,
            right: 0,
            value: ConditionValue::None,
        },
        ConditionNode {
            op: ConditionOp::ControlApproved,
            left: 0,
            right: 0,
            value: ConditionValue::ControlType(ControlType::HumanReview),
        },
        ConditionNode {
            op: ConditionOp::And,
            left: 0,
            right: 1,
            value: ConditionValue::None,
        },
    ];
    let rules = [
        CompiledRule {
            rule_id_hash: sha256(b"rule-1"),
            priority: 100,
            root: 3,
            effect: RuleEffect {
                decision: Decision::Block,
                reason: reason(b"HUMAN_REVIEW_REQUIRED"),
            },
        },
        CompiledRule {
            rule_id_hash: sha256(b"rule-2"),
            priority: 50,
            root: 2,
            effect: RuleEffect {
                decision: Decision::Pass,
                reason: reason(b"HUMAN_REVIEW_PRESENT"),
            },
        },
    ];
    (nodes, rules)
}

fn demo_policy<'a>(
    nodes: &'a [ConditionNode],
    rules: &'a [CompiledRule<'a>],
) -> CompiledPolicy<'a> {
    CompiledPolicy {
        policy_id: identifier(b"action-gate"),
        policy_version: identifier(b"0.6"),
        policy_hash: sha256(b"policy"),
        nodes,
        rules,
        default_effect: RuleEffect {
            decision: Decision::Warn,
            reason: reason(b"ELEVATED_RISK"),
        },
    }
}

fn approved_human_review() -> ControlObservation {
    ControlObservation {
        control_type: ControlType::HumanReview,
        action_hash: sha256(b"action"),
        status: ControlStatus::Approved,
        actor_hash: sha256(b"reviewer"),
        observed_at: TimestampUtc::new(1_720_000_000, 0).unwrap(),
        evidence_hash: Some(sha256(b"control")),
    }
}

fn artifact_ref() -> ArtifactRef<'static> {
    ArtifactRef {
        artifact_type: ArtifactType::ActionProposal,
        media_type: MediaType::ApplicationJson,
        path_hash: sha256(b"action.json"),
        size_bytes: 128,
        content_hash: sha256(b"artifact"),
        schema_hash: Some(sha256(b"schema")),
        path_hint: text(b"action.json"),
    }
}

static DEMO_REASON_SLOTS: [ReasonCodeSlot<'static>; 1] = [ReasonCodeSlot {
    bytes: b"RUNTIME_DETERMINISTIC_DEMO",
}];

fn build_demo_payload() -> crate::receipt::ReceiptPayload<'static> {
    let payload = crate::receipt::ReceiptPayload {
        schema_version: crate::receipt::ReceiptSchemaVersion::V2,
        receipt_id: identifier(b"urn:ink:receipt:test"),
        receipt_profile: crate::receipt::ReceiptProfile::ThinWaistV2,
        action_id: identifier(b"urn:ink:action:test"),
        issued_at: TimestampUtc::new(1_720_000_000, 42).unwrap(),
        issuer: IssuerClaim {
            name: text(b"BLKBX Lab"),
            key_id: identifier(b"ed25519:demo"),
            public_key: Ed25519PublicKey(
                SigningKey::from_bytes(&[7u8; 32])
                    .verifying_key()
                    .to_bytes(),
            ),
        },
        manifest_hash: sha256(b"manifest"),
        policy: PolicyBinding {
            policy_id: identifier(b"action-gate"),
            policy_version: identifier(b"0.6"),
            policy_hash: sha256(b"policy"),
        },
        model: demo_model(),
        facts: PolicyFacts {
            requires_human_review: false,
            ..demo_facts()
        },
        decision: Decision::Pass,
        reasons: &DEMO_REASON_SLOTS,
        evidence_summary_hash: sha256(b"evidence-summary"),
        controls_summary_hash: sha256(b"controls-summary"),
    };
    payload.validate().unwrap();
    payload
}

#[test]
fn bounded_bytes_reject_invalid_inputs() {
    let long = [b'a'; 9];
    assert_eq!(BoundedBytes::<8>::new(b""), Err(Error::EmptyValue));
    assert_eq!(BoundedBytes::<8>::new(&long), Err(Error::ValueTooLong));
    assert_eq!(
        BoundedBytes::<16>::new(b"abc\0def"),
        Err(Error::ContainsNul)
    );
    assert_eq!(
        BoundedBytes::<16>::new_identifier(b"bad space"),
        Err(Error::InvalidByteClass)
    );
    assert_eq!(
        BoundedBytes::<16>::new_reason_code(b"bad reason"),
        Err(Error::InvalidByteClass)
    );
}

#[test]
fn timestamp_rejects_invalid_nanos() {
    assert_eq!(
        TimestampUtc::new(1_720_000_000, 1_000_000_000),
        Err(Error::InvalidTimestamp)
    );
}

#[test]
fn manifest_binding_rejects_artifact_overflow() {
    let artifacts = [artifact_ref(); MAX_ARTIFACTS + 1];
    let binding = ManifestBinding {
        action_id: identifier(b"urn:ink:action:test"),
        manifest_hash: sha256(b"manifest"),
        artifacts: &artifacts,
    };
    assert_eq!(binding.validate(), Err(Error::TooManyArtifacts));
}

#[test]
fn manifest_binding_rejects_empty_artifacts() {
    let artifacts: [ArtifactRef<'static>; 0] = [];
    let binding = ManifestBinding {
        action_id: identifier(b"urn:ink:action:test"),
        manifest_hash: sha256(b"manifest"),
        artifacts: &artifacts,
    };
    assert_eq!(binding.validate(), Err(Error::EmptyValue));
}

#[test]
fn control_set_rejects_control_overflow() {
    let controls = [approved_human_review(); MAX_CONTROLS + 1];
    assert_eq!(ControlSet::new(&controls), Err(Error::TooManyControls));
}

#[test]
fn compiled_policy_rejects_bad_root() {
    let nodes = [ConditionNode {
        op: ConditionOp::Always,
        left: 0,
        right: 0,
        value: ConditionValue::None,
    }];
    let rules = [CompiledRule {
        rule_id_hash: sha256(b"rule"),
        priority: 10,
        root: 1,
        effect: RuleEffect {
            decision: Decision::Pass,
            reason: reason(b"DEFAULT_PASS"),
        },
    }];
    let policy = demo_policy(&nodes, &rules);
    assert_eq!(policy.validate(), Err(Error::InvalidRuleRoot));
}

#[test]
fn compiled_policy_rejects_bad_child_index_and_shape() {
    let bad_child_nodes = [ConditionNode {
        op: ConditionOp::Not,
        left: 4,
        right: 0,
        value: ConditionValue::None,
    }];
    let bad_shape_nodes = [ConditionNode {
        op: ConditionOp::RuntimeKindEquals,
        left: 0,
        right: 0,
        value: ConditionValue::Bool(true),
    }];
    let rules = [CompiledRule {
        rule_id_hash: sha256(b"rule"),
        priority: 10,
        root: 0,
        effect: RuleEffect {
            decision: Decision::Pass,
            reason: reason(b"DEFAULT_PASS"),
        },
    }];
    assert_eq!(
        demo_policy(&bad_child_nodes, &rules).validate(),
        Err(Error::InvalidConditionShape)
    );
    assert_eq!(
        demo_policy(&bad_shape_nodes, &rules).validate(),
        Err(Error::InvalidConditionShape)
    );
}

#[test]
fn compiled_policy_rejects_cycles() {
    let nodes = [
        ConditionNode {
            op: ConditionOp::Not,
            left: 1,
            right: 0,
            value: ConditionValue::None,
        },
        ConditionNode {
            op: ConditionOp::Not,
            left: 0,
            right: 0,
            value: ConditionValue::None,
        },
    ];
    let rules = [CompiledRule {
        rule_id_hash: sha256(b"rule"),
        priority: 10,
        root: 0,
        effect: RuleEffect {
            decision: Decision::Pass,
            reason: reason(b"DEFAULT_PASS"),
        },
    }];
    assert_eq!(
        demo_policy(&nodes, &rules).validate(),
        Err(Error::InvalidConditionCycle)
    );
}

#[test]
fn policy_bool_leaf_respects_false_value() {
    let nodes = [ConditionNode {
        op: ConditionOp::ProviderFallbacksAllowed,
        left: 0,
        right: 0,
        value: ConditionValue::Bool(false),
    }];
    let rules = [CompiledRule {
        rule_id_hash: sha256(b"rule"),
        priority: 10,
        root: 0,
        effect: RuleEffect {
            decision: Decision::Pass,
            reason: reason(b"FALLBACKS_DISABLED"),
        },
    }];
    let policy = demo_policy(&nodes, &rules);
    let facts = PolicyFacts {
        provider_fallbacks_allowed: false,
        requires_human_review: false,
        ..demo_facts()
    };
    let controls: [ControlObservation; 0] = [];
    let mut reason_slots = [ReasonCodeSlot { bytes: b"" }; 2];
    let mut out = EvaluationOut {
        decision: Decision::Warn,
        reasons: ReasonWriter {
            buf: &mut reason_slots,
            len: 0,
        },
    };
    evaluate_policy(
        PolicyInput {
            facts,
            controls: ControlSet::new(&controls).unwrap(),
        },
        policy,
        &mut out,
    )
    .unwrap();
    assert_eq!(out.decision, Decision::Pass);
}

#[test]
fn model_waist_rejects_requested_output_mismatch() {
    let mut model = demo_model();
    model.invocation.response_schema_hash = Some(sha256(b"wrong-schema"));
    assert_eq!(model.validate(), Err(Error::InvalidRequestedOutputShape));
}

#[test]
fn model_waist_rejects_invalid_token_usage_totals() {
    let mut model = demo_model();
    model.observation.usage.total_tokens = Some(10);
    assert_eq!(model.validate(), Err(Error::InvalidTokenUsageTotals));
}

#[test]
fn runtime_claim_rejects_invalid_shapes() {
    let mut hosted_topology = demo_model().runtime;
    hosted_topology.runtime_kind = RuntimeKind::HostedModelApi;
    assert_eq!(hosted_topology.validate(), Err(Error::InvalidRuntimeShape));

    let mut bad_determinism = demo_model().runtime;
    bad_determinism.runtime_kind = RuntimeKind::LocalOpenWeightModel;
    bad_determinism.execution_topology = ExecutionTopology::LocalProcess;
    bad_determinism.determinism = DeterminismClaim {
        deterministic: false,
        seed_bound: true,
    };
    assert_eq!(bad_determinism.validate(), Err(Error::InvalidRuntimeShape));

    let mut weak_demo = demo_model().runtime;
    weak_demo.replay_strength = ReplayStrength::DeclaredOnly;
    assert_eq!(weak_demo.validate(), Err(Error::InvalidRuntimeShape));
}

#[test]
fn model_waist_rejects_replay_model_non_replay_runtime() {
    let mut model = demo_model();
    model.identity.model_class = ModelClass::Replay;
    assert_eq!(model.validate(), Err(Error::InvalidModelShape));
}

#[test]
fn policy_requires_human_review_without_control() {
    let (nodes, rules) = demo_policy_parts();
    let facts = demo_facts();
    let controls: [ControlObservation; 0] = [];
    let mut slots = [ReasonCodeSlot { bytes: b"" }; 4];
    let mut out = EvaluationOut {
        decision: Decision::Warn,
        reasons: ReasonWriter {
            buf: &mut slots,
            len: 0,
        },
    };
    evaluate_policy(
        PolicyInput {
            facts,
            controls: ControlSet::new(&controls).unwrap(),
        },
        demo_policy(&nodes, &rules),
        &mut out,
    )
    .unwrap();
    assert_eq!(out.decision, Decision::Block);
    assert_eq!(out.reasons.as_slice()[0].bytes, b"HUMAN_REVIEW_REQUIRED");
}

#[test]
fn receipt_rejects_inconsistent_facts() {
    let mut reason_slots = [ReasonCodeSlot { bytes: b"" }; 2];
    let mut evaluation = EvaluationOut {
        decision: Decision::Pass,
        reasons: ReasonWriter {
            buf: &mut reason_slots,
            len: 0,
        },
    };
    evaluation
        .reasons
        .push(reason(b"RUNTIME_DETERMINISTIC_DEMO"))
        .unwrap();
    let result = build_receipt_payload(
        ReceiptInput {
            receipt_id: identifier(b"urn:ink:receipt:test"),
            action_id: identifier(b"urn:ink:action:test"),
            issued_at: TimestampUtc::new(1_720_000_000, 0).unwrap(),
            issuer: IssuerClaim {
                name: text(b"BLKBX Lab"),
                key_id: identifier(b"ed25519:demo"),
                public_key: Ed25519PublicKey(
                    SigningKey::from_bytes(&[7u8; 32])
                        .verifying_key()
                        .to_bytes(),
                ),
            },
            manifest_hash: sha256(b"manifest"),
            policy: PolicyBinding {
                policy_id: identifier(b"action-gate"),
                policy_version: identifier(b"0.6"),
                policy_hash: sha256(b"policy"),
            },
            model: demo_model(),
            facts: PolicyFacts {
                runtime_kind: RuntimeKind::HostedModelApi,
                ..demo_facts()
            },
            evidence_summary_hash: sha256(b"evidence-summary"),
            controls_summary_hash: sha256(b"controls-summary"),
        },
        &evaluation,
    );
    assert_eq!(result, Err(Error::InconsistentReceiptPayload));
}

#[test]
fn verified_summary_rejects_invalid_payload() {
    let mut payload = build_demo_payload();
    payload.facts.runtime_kind = RuntimeKind::HostedModelApi;
    assert_eq!(
        VerifiedReceiptSummary::from_payload(&payload),
        Err(Error::InconsistentReceiptPayload)
    );
}

#[test]
fn transcript_hash_is_stable_for_fixed_fixture() {
    let payload = build_demo_payload();
    assert_eq!(
        receipt_transcript_hash(&payload).unwrap(),
        Sha256Digest([
            156, 166, 147, 125, 27, 63, 31, 220, 168, 10, 25, 200, 47, 72, 181, 246, 16, 102, 11,
            5, 145, 174, 160, 144, 52, 149, 15, 123, 33, 255, 6, 234,
        ])
    );
    assert_ne!(
        runtime_claim_hash(payload.model.runtime),
        Sha256Digest::ZERO
    );
    assert_ne!(model_waist_hash(payload.model).unwrap(), Sha256Digest::ZERO);
    assert_ne!(policy_facts_hash(payload.facts), Sha256Digest::ZERO);
}

#[test]
fn signature_round_trip_and_mismatch() {
    let key = SigningKey::from_bytes(&[7u8; 32]);
    let wrong_key = SigningKey::from_bytes(&[9u8; 32]);
    let payload = build_demo_payload();
    let signature = sign_receipt_payload(&payload, &key).unwrap();
    let mut verification = VerificationOut {
        valid: false,
        payload_hash: Sha256Digest::ZERO,
        reason: VerificationReason::InvalidSignature,
    };
    verify_receipt(
        &payload,
        &signature,
        &Ed25519PublicKey(key.verifying_key().to_bytes()),
        &mut verification,
    )
    .unwrap();
    assert!(verification.valid);
    verify_receipt(
        &payload,
        &signature,
        &Ed25519PublicKey(wrong_key.verifying_key().to_bytes()),
        &mut verification,
    )
    .unwrap();
    assert!(!verification.valid);
    assert_eq!(verification.reason, VerificationReason::InvalidSignature);
}

#[test]
fn comparison_checks_matching_and_non_matching_actions() {
    let left = VerifiedReceiptSummary {
        receipt_id: identifier(b"left"),
        action_id: identifier(b"action"),
        action_hash: sha256(b"same-action"),
        manifest_hash: sha256(b"left-manifest"),
        decision: Decision::Block,
        payload_hash: sha256(b"left-payload"),
    };
    let right = VerifiedReceiptSummary {
        receipt_id: identifier(b"right"),
        action_id: identifier(b"action"),
        action_hash: sha256(b"same-action"),
        manifest_hash: sha256(b"right-manifest"),
        decision: Decision::Block,
        payload_hash: sha256(b"right-payload"),
    };
    let mut out = ComparisonOut {
        comparable: false,
        decision_match: false,
        action_match: false,
        manifest_match: false,
    };
    compare_receipts(left, right, &mut out).unwrap();
    assert!(out.comparable);
    assert!(out.action_match);
    assert!(!out.manifest_match);

    let mismatch = VerifiedReceiptSummary {
        action_hash: sha256(b"different-action"),
        ..right
    };
    compare_receipts(left, mismatch, &mut out).unwrap();
    assert!(!out.comparable);
    assert!(!out.action_match);
    assert!(!out.decision_match);
}
