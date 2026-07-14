use crate::signing::{verify_receipt_signature, ReceiptSigner};
use crate::types::{Ed25519PublicKey, Ed25519Signature, ActionId, ReceiptId, TimestampUtc, Sha256Digest, KeyId, BoundedBytes};
use crate::receipt::{ReceiptPayload, ReceiptSchemaVersion, ReceiptProfile};
use crate::policy::{Decision, PolicyFacts, PolicyBinding};
use crate::model_waist::{ModelWaist, RuntimeClaim, PluginClaim, ModelIdentityClaim, ModelInvocationClaim, ModelObservationClaim, RequestedOutput, DeterminismClaim, IsolationClaim, ProviderRoutingClaim, ReplayStrength, RuntimeKind, ExecutionTopology, MaintainerClass, ModelClass, PluginTrustLevel, DataCollectionPolicy, NormalizationClaim, FinishReason, TokenUsage, PluginApiVersion, IdentityEvidence};
use crate::error::Error;
use crate::types::{KeyId as KeyIdType, BoundedBytes as BoundedBytesType, Ed25519PublicKey as PubKey};
use rand::rngs::OsRng;
use ed25519_dalek::{SigningKey, Signer, Verifier};
use core::convert::TryFrom;

// Mock signer for testing
struct MockSigner;

impl ReceiptSigner for MockSigner {
    fn sign_digest(&self, _digest: &[u8; 32]) -> Result<Ed25519Signature, Error> {
        // Simple deterministic signature for testing
        Ok(Ed25519Signature([0u8; 64]))
    }
}

// Integration test for signing and verification
#[test]
fn test_integration_signing_verification() {
    // Create a mock payload with all required fields
    let payload = ReceiptPayload {
        schema_version: ReceiptSchemaVersion::V2,
        receipt_id: ReceiptId::new_identifier(b"test_receipt").unwrap(),
        receipt_profile: ReceiptProfile::ThinWaistV2,
        action_id: ActionId::new_identifier(b"test_action").unwrap(),
        issued_at: TimestampUtc::new(0, 0).unwrap(),
        issuer: crate::receipt::IssuerClaim {
            name: BoundedBytes::new_identifier(b"test_issuer").unwrap(),
            key_id: KeyId::new_identifier(b"test_key").unwrap(),
            public_key: Ed25519PublicKey([0u8; 32]),
        },
        manifest_hash: Sha256Digest([0u8; 32]),
        policy: PolicyBinding {
            policy_id: BoundedBytes::new_identifier(b"test_policy").unwrap(),
            policy_version: BoundedBytes::new_identifier(b"v1").unwrap(),
            policy_hash: Sha256Digest([0u8; 32]),
        },
        model: ModelWaist {
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
                runtime_kind: RuntimeKind::Local,
                execution_topology: ExecutionTopology::SingleProcess,
                replay_strength: ReplayStrength::Deterministic,
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
                plugin_id_hash: Sha256Digest([0u8; 32]),
                plugin_version_hash: Sha256Digest([0u8; 32]),
                plugin_api_version: PluginApiVersion::V1,
                maintainer_class: MaintainerClass::FirstParty,
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
        },
        facts: PolicyFacts {
            risk_class: crate::policy::RiskClass::Low,
            requires_human_review: false,
            binding_effect_present: false,
            provider_fallbacks_allowed: false,
            plugin_trust_level: crate::policy::PluginTrustFact::FirstPartyReference,
            runtime_kind: RuntimeKind::Local,
            replay_strength: ReplayStrength::Deterministic,
            model_class: ModelClass::OpenWeight,
        },
        decision: Decision::Accept,
        reasons: &[crate::policy::ReasonCodeSlot {
            bytes: BoundedBytes::new_reason_code(b"test_reason").unwrap(),
        }],
        evidence_summary_hash: Sha256Digest([0u8; 32]),
        controls_summary_hash: Sha256Digest([0u8; 32]),
    };

    // Test signing
    let signer = MockSigner;
    let signature = signer.sign_digest(&[0u8; 32]).unwrap();
    
    // Test verification (should succeed with correct signature)
    let result = verify_receipt_signature(&payload, &signature, &Ed25519PublicKey([0u8; 32]));
    assert!(result.is_ok(), "Verification should succeed with valid signature");

    // Test verification with wrong public key (should fail)
    let wrong_pub_key = Ed25519PublicKey([1u8; 32]);
    let result = verify_receipt_signature(&payload, &signature, &wrong_pub_key);
    assert!(result.is_err(), "Verification should fail with invalid public key");
}

#[test]
fn test_signing_key_functionality() {
    // Test that SigningKey can sign a digest
    let mut rng = OsRng;
    let key = SigningKey::generate(&mut rng);
    let digest = [0u8; 32];
    let signature = key.sign(&digest);
    assert!(!signature.to_bytes().is_empty(), "Signature should not be empty");
    
    // Verify that the signature can be verified
    let verifying_key = key.verifying_key();
    let valid = verifying_key.verify(&digest, &signature);
    assert!(valid.is_ok(), "Verification should succeed with correct key");
}
