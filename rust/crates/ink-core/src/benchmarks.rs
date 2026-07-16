//! Benchmarking module for performance testing of critical paths.
//!
//! This module provides benchmarks for:
//! - Hashing operations (parallel and sequential)
//! - Policy evaluation performance
//! - Memory allocation patterns
//! - Receipt processing throughput

use std::time::Instant;

use crate::digest::{parallel_sha256, sha256};
use crate::policy::{PolicyFacts, PolicyInput, CompiledPolicy, EvaluationOut};
use crate::model_waist::{ModelWaist, RuntimeClaim, RuntimeKind, ExecutionTopology, ReplayStrength};
use crate::model_waist::{DeterminismClaim, IsolationClaim, ProviderRoutingClaim};
use crate::model_waist::{DataCollectionPolicy, PluginClaim, PluginApiVersion, MaintainerClass};
use crate::model_waist::{NormalizationClaim, PluginTrustLevel, ModelIdentityClaim, ModelClass};
use crate::model_waist::{IdentityEvidence, ModelInvocationClaim, ModelObservationClaim};
use crate::model_waist::{RequestedOutput, FinishReason, TokenUsage};
use crate::types::{Sha256Digest, BoundedBytes};
use crate::receipt::{ReceiptPayload, ReceiptSchemaVersion, ReceiptProfile};
use crate::receipt::{IssuerClaim, PolicyBinding};
use crate::policy::Decision;

/// Benchmark parallel vs sequential hashing performance
pub fn benchmark_hashing() {
    let data: Vec<Vec<u8>> = vec![
        b"test data 1".to_vec(),
        b"test data 2".to_vec(),
        b"test data 3".to_vec(),
        b"test data 4".to_vec(),
        b"test data 5".to_vec(),
    ];

    let data_refs: Vec<&[u8]> = data.iter().map(|v| v.as_slice()).collect();

    // Benchmark sequential hashing
    let start = Instant::now();
    let mut sequential_results: Vec<Sha256Digest> = Vec::new();
    for d in &data_refs {
        sequential_results.push(sha256(d));
    }
    let sequential_time = start.elapsed();

    // Benchmark parallel hashing
    let start = Instant::now();
    let parallel_results = parallel_sha256(&data_refs);
    let parallel_time = start.elapsed();

    println!("Sequential hashing: {:.2?} for {} items", sequential_time, data.len());
    println!("Parallel hashing: {:.2?} for {} items", parallel_time, data.len());
    println!("Speedup: {:.2}x", sequential_time.as_nanos() as f64 / parallel_time.as_nanos() as f64);
}

/// Benchmark policy evaluation performance
pub fn benchmark_policy_evaluation() {
    // Create a simple policy facts
    let facts = PolicyFacts {
        risk_class: crate::policy::RiskClass::Low,
        requires_human_review: false,
        binding_effect_present: false,
        provider_fallbacks_allowed: false,
        plugin_trust_level: crate::policy::PluginTrustFact::Untrusted,
        runtime_kind: RuntimeKind::LocalOpenWeightModel,
        replay_strength: ReplayStrength::DeclaredOnly,
        model_class: ModelClass::OpenWeight,
    };

    // Create a simple model waist
    let model = ModelWaist {
        identity: ModelIdentityClaim {
            model_class: ModelClass::OpenWeight,
            model_ref_hash: Sha256Digest([0u8; 32]),
            model_slug: BoundedBytes::new_identifier(b"test_model").unwrap(),
            identity_evidence: IdentityEvidence::Declared,
        },
        invocation: ModelInvocationClaim {
            action_hash: Sha256Digest([0u8; 32]),
            messages_hash: Sha256Digest([0u8; 32]),
            system_prompt_hash: None,
            tool_spec_hash: None,
            response_schema_hash: None,
            parameters_hash: Sha256Digest([0u8; 32]),
            requested_output: RequestedOutput::FreeText,
        },
        observation: ModelObservationClaim {
            output_text_hash: None,
            structured_output_hash: None,
            provider_metadata_hash: None,
            finish_reason: FinishReason::Stop,
            usage: TokenUsage {
                input_tokens: None,
                output_tokens: None,
                total_tokens: None,
            },
        },
        runtime: RuntimeClaim {
            runtime_kind: RuntimeKind::LocalOpenWeightModel,
            execution_topology: ExecutionTopology::LocalProcess,
            replay_strength: ReplayStrength::DeclaredOnly,
            determinism: DeterminismClaim {
                deterministic: true,
                seed_bound: false,
            },
            isolation: IsolationClaim {
                process_isolated: false,
            },
            provider_routing: ProviderRoutingClaim {
                fallbacks_allowed: false,
                provider_pinned: false,
                data_collection_policy: DataCollectionPolicy::DeclaredDeny,
            },
        },
        plugin: PluginClaim {
            plugin_id_hash: Sha256Digest([0u8; 32]),
            plugin_version_hash: Sha256Digest([0u8; 32]),
            plugin_api_version: PluginApiVersion::V1,
            maintainer_class: MaintainerClass::FirstPartyReference,
            normalization: NormalizationClaim {
                input_normalized: true,
                output_normalized: true,
                raw_request_preserved: true,
                raw_response_preserved: true,
                secrets_redacted: true,
            },
            plugin_manifest_hash: Sha256Digest([0u8; 32]),
            plugin_id_hint: BoundedBytes::new_identifier(b"test_plugin").unwrap(),
            trust_level: PluginTrustLevel::FirstPartyReference,
        },
    };

    // Create a simple policy input
    let input = PolicyInput {
        facts,
        controls: crate::controls::ControlSet::new(&[]).unwrap(),
    };

    // Create a simple compiled policy (just a placeholder)
    let policy = CompiledPolicy {
        policy_id: BoundedBytes::new_identifier(b"test_policy").unwrap(),
        policy_version: BoundedBytes::new_identifier(b"v1").unwrap(),
        policy_hash: Sha256Digest([0u8; 32]),
        nodes: &[],
        rules: &[],
        default_effect: crate::policy::RuleEffect {
            decision: Decision::Pass,
            reason: BoundedBytes::new_reason_code(b"default").unwrap(),
        },
    };

    // Benchmark policy evaluation
    let mut out = EvaluationOut {
        decision: Decision::Pass,
        reasons: crate::policy::ReasonWriter {
            buf: &mut [],
            len: 0,
        },
    };

    let start = Instant::now();
    for _ in 0..1000 {
        let _ = crate::policy::evaluate_policy(input, policy, &mut out);
    }
    let eval_time = start.elapsed();

    println!("Policy evaluation: {:.2?} for 1000 iterations", eval_time);
    println!("Average per evaluation: {:.2?}", eval_time / 1000);
}

#[cfg(feature = "std")]
/// Benchmark receipt processing performance
pub fn benchmark_receipt_processing() {
    // Create a simple receipt payload
    let payload = ReceiptPayload {
        schema_version: ReceiptSchemaVersion::V2,
        receipt_id: BoundedBytes::new_identifier(b"test_receipt").unwrap(),
        receipt_profile: ReceiptProfile::ThinWaistV2,
        action_id: BoundedBytes::new_identifier(b"test_action").unwrap(),
        issued_at: crate::types::TimestampUtc::new(0, 0).unwrap(),
        issuer: IssuerClaim {
            name: BoundedBytes::new_identifier(b"test_issuer").unwrap(),
            key_id: BoundedBytes::new_identifier(b"test_key").unwrap(),
            public_key: crate::types::Ed25519PublicKey([0u8; 32]),
        },
        manifest_hash: Sha256Digest([0u8; 32]),
        policy: PolicyBinding {
            policy_id: BoundedBytes::new_identifier(b"test_policy").unwrap(),
            policy_version: BoundedBytes::new_identifier(b"v1").unwrap(),
            policy_hash: Sha256Digest([0u8; 32]),
        },
        model: model.clone(),
        facts: PolicyFacts {
            risk_class: crate::policy::RiskClass::Low,
            requires_human_review: false,
            binding_effect_present: false,
            provider_fallbacks_allowed: false,
            plugin_trust_level: crate::policy::PluginTrustFact::Untrusted,
            runtime_kind: RuntimeKind::LocalOpenWeightModel,
            replay_strength: ReplayStrength::DeclaredOnly,
            model_class: ModelClass::OpenWeight,
        },
        decision: Decision::Pass,
        reasons: &[],
        evidence_summary_hash: Sha256Digest([0u8; 32]),
        controls_summary_hash: Sha256Digest([0u8; 32]),
    };

    // Benchmark receipt validation
    let start = Instant::now();
    for _ in 0..100 {
        let _ = payload.validate();
    }
    let validation_time = start.elapsed();

    println!("Receipt validation: {:.2?} for 100 iterations", validation_time);
    println!("Average per validation: {:.2?}", validation_time / 100);
}

/// Run all benchmarks
pub fn run_all_benchmarks() {
    println!("=== Rust Core Performance Benchmarks ===\n");
    benchmark_hashing();
    println!();
    benchmark_policy_evaluation();
    println!();
    benchmark_receipt_processing();
    println!("\n=== Benchmark Complete ===");
}