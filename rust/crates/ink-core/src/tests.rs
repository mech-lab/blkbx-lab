use proptest::prelude::*;
use super::*;
use ink_core::signing::{sign_receipt_payload, verify_receipt_signature};
use ink_core::types::{Ed25519PublicKey, Ed25519Signature, ReceiptPayload};
use ink_core::signing::ReceiptSigner;
use std::convert::TryFrom;

// Mock signer for testing
struct MockSigner;

impl ReceiptSigner for MockSigner {
    fn sign_digest(&self, digest: &[u8; 32]) -> Result<Ed25519Signature, Error> {
        // Simple deterministic signature for testing
        Ok(Ed25519Signature([0u8; 64]))
    }
}

// Integration test for signing and verification
#[test]
fn test_integration_signing_verification() {
    // Create a mock payload
    let payload = ReceiptPayload {
        // Minimal payload for testing
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
    let key = ed25519_dalek::SigningKey::new(ed25519_dalek::rand::rngs::OsRng {});
    let digest = [0u8; 32];
    let signature = key.sign(&digest);
    assert!(!signature.to_bytes().is_empty(), "Signature should not be empty");
    
    // Verify that the signature can be verified
    let verifying_key = key.verifying_key();
    let valid = verifying_key.verify(&digest, &signature);
    assert!(valid.is_ok(), "Verification should succeed with correct key");
}
