#![forbid(unsafe_code)]

use ed25519_dalek::{Signer, SigningKey};
use ink_core::bounded::{DomainTag, IssuerId, PublicKeyId, SchemaAuthority, SchemaId, SubjectId};
use ink_core::{
    canon, hash, AttestationEnvelope, Claim, Digest, Evidence, ParentHashes, Policy,
    PolicyDecision, ReceiptEnvelope, Schema, SignatureProfileId, ValidityWindow,
};
use ink_sign::attest_receipt;
use ink_verify::{ReceiptStatus, TrustedIssuerKey, VerificationCode};

pub const PUBLIC_RECEIPT_VECTORS_JSON: &str =
    include_str!("../../../../test-vectors/ink-vectors.json");

#[derive(Debug, Clone)]
pub struct ReceiptVector {
    pub name: &'static str,
    pub human_fixture: &'static str,
    pub canonical_bytes_hex: String,
    pub body_hash_hex: String,
    pub schema_hash_hex: String,
    pub evidence_hash_hex: String,
    pub expected_verify: bool,
}

#[derive(Debug, Clone)]
pub struct KernelVerificationVector {
    pub name: &'static str,
    pub receipt_bytes_hex: String,
    pub trusted_keys: Vec<TrustedIssuerKey>,
    pub allow_unsigned: bool,
    pub current_sequence: Option<u64>,
    pub expected_status: ReceiptStatus,
    pub expected_code: VerificationCode,
    pub expected_structural_valid: bool,
}

#[derive(Debug, Clone)]
pub struct KernelDecodeVector {
    pub name: &'static str,
    pub receipt_bytes_hex: String,
    pub expected_error: &'static str,
}

pub fn minimal_receipt_vector() -> ReceiptVector {
    let schema = Schema::from_slice(
        SchemaId::from_str("ink.receipt.test.v1").unwrap(),
        SchemaAuthority::from_str("ink").unwrap(),
        DomainTag::from_str("test").unwrap(),
        1,
        b"{\"kind\":\"minimal\"}",
    )
    .unwrap();
    let claim = Claim::from_slice(
        schema.id,
        SubjectId::from_str("subject-1").unwrap(),
        b"claim",
    )
    .unwrap();
    let evidence = Evidence::from_slice(schema.id, b"evidence").unwrap();
    let policy = Policy::from_slice(schema.id, PolicyDecision::Pass, b"policy").unwrap();
    let receipt = ReceiptEnvelope::create(
        schema.id,
        schema.compute_hash().unwrap(),
        schema.authority,
        schema.domain_tag,
        claim.compute_hash().unwrap(),
        IssuerId::from_str("issuer-1").unwrap(),
        1,
        claim.compute_hash().unwrap(),
        evidence.compute_hash().unwrap(),
        policy.compute_hash().unwrap(),
        Digest::new([9u8; 32]),
        ParentHashes::new(),
    )
    .seal()
    .unwrap();
    let mut bytes = [0u8; 512];
    let len = canon::encode_receipt(&receipt, &mut bytes).unwrap();
    ReceiptVector {
        name: "minimal_valid_receipt",
        human_fixture: "minimal valid receipt",
        canonical_bytes_hex: hex::encode(&bytes[..len]),
        body_hash_hex: hex::encode(receipt.body_hash.0),
        schema_hash_hex: hex::encode(schema.compute_hash().unwrap().0),
        evidence_hash_hex: hex::encode(evidence.compute_hash().unwrap().0),
        expected_verify: true,
    }
}

pub fn superseded_receipt_vector() -> ReceiptVector {
    let mut vector = minimal_receipt_vector();
    vector.name = "superseded_lifecycle";
    vector.human_fixture = "receipt with superseded lifecycle";
    vector
}

pub fn kernel_verification_vectors() -> Vec<KernelVerificationVector> {
    let (base_receipt, trusted_key, signing_key, public_key_id) = seeded_signed_fixture();
    let signed_receipt = attest_receipt(
        base_receipt,
        SignatureProfileId::InkSigEd25519V1,
        public_key_id,
        &signing_key,
        None,
    )
    .unwrap();
    let trusted_key_bytes = vec![trusted_key];

    let mut vectors = Vec::new();
    vectors.push(kernel_vector(
        "valid_signed_receipt",
        signed_receipt,
        trusted_key_bytes.clone(),
        true,
        None,
        ReceiptStatus::SignatureValid,
        VerificationCode::SignatureValid,
        true,
    ));
    vectors.push(kernel_vector(
        "valid_unsigned_receipt",
        base_receipt,
        Vec::new(),
        true,
        None,
        ReceiptStatus::StructuralValidUnsigned,
        VerificationCode::StructuralValidUnsigned,
        true,
    ));
    vectors.push(kernel_vector(
        "missing_signature",
        base_receipt,
        Vec::new(),
        false,
        None,
        ReceiptStatus::SignatureMissing,
        VerificationCode::SignatureMissing,
        true,
    ));

    let mut invalid_signature = signed_receipt;
    invalid_signature.attestation.as_mut().unwrap().signature.0[0] ^= 0x55;
    vectors.push(kernel_vector(
        "invalid_signature",
        invalid_signature,
        trusted_key_bytes.clone(),
        true,
        None,
        ReceiptStatus::SignatureInvalid,
        VerificationCode::InvalidSignature,
        false,
    ));

    let wrong_key = TrustedIssuerKey {
        public_key: ink_core::Ed25519PublicKey([9u8; 32]),
        ..trusted_key
    };
    vectors.push(kernel_vector(
        "wrong_issuer_key",
        signed_receipt,
        vec![wrong_key],
        true,
        None,
        ReceiptStatus::SignatureInvalid,
        VerificationCode::InvalidSignature,
        true,
    ));

    let mut modified_receipt_body = signed_receipt;
    modified_receipt_body.claim_hash = Digest::new([0xAB; 32]);
    vectors.push(kernel_vector(
        "modified_receipt_body",
        modified_receipt_body,
        trusted_key_bytes.clone(),
        true,
        None,
        ReceiptStatus::SignatureInvalid,
        VerificationCode::SignedMessageHashMismatch,
        false,
    ));

    let mut modified_schema_hash = signed_receipt;
    modified_schema_hash.schema_hash = Digest::new([0xCD; 32]);
    vectors.push(kernel_vector(
        "modified_schema_hash",
        modified_schema_hash,
        trusted_key_bytes.clone(),
        true,
        None,
        ReceiptStatus::SignatureInvalid,
        VerificationCode::SignedMessageHashMismatch,
        false,
    ));

    let unsupported_profile = base_receipt
        .with_attestation(AttestationEnvelope {
            profile_id: SignatureProfileId::Unknown(0x44),
            issuer_id: base_receipt.issuer_id,
            public_key_id,
            signature: ink_core::Ed25519Signature([7u8; 64]),
            signed_message_hash: Digest::new([8u8; 32]),
            sequence: base_receipt.sequence,
            validity_window: None,
        })
        .unwrap();
    vectors.push(kernel_vector(
        "unsupported_algorithm",
        unsupported_profile,
        trusted_key_bytes.clone(),
        true,
        None,
        ReceiptStatus::SignatureUnsupported,
        VerificationCode::SignatureUnsupported,
        true,
    ));

    let noncanonical_hash =
        hash::hash_bytes(ink_core::HashAlgorithm::Sha256, b"NONCANONICAL").unwrap();
    let noncanonical_signed_payload = base_receipt
        .with_attestation(AttestationEnvelope {
            profile_id: SignatureProfileId::InkSigEd25519V1,
            issuer_id: base_receipt.issuer_id,
            public_key_id,
            signature: ink_core::Ed25519Signature(
                signing_key.sign(noncanonical_hash.as_bytes()).to_bytes(),
            ),
            signed_message_hash: noncanonical_hash,
            sequence: base_receipt.sequence,
            validity_window: None,
        })
        .unwrap();
    vectors.push(kernel_vector(
        "noncanonical_signed_payload",
        noncanonical_signed_payload,
        trusted_key_bytes.clone(),
        true,
        None,
        ReceiptStatus::SignatureInvalid,
        VerificationCode::SignedMessageHashMismatch,
        true,
    ));

    let wrong_domain_hash =
        hash::hash_bytes(ink_core::HashAlgorithm::Sha256, b"WRONG-DOMAIN-SEPARATOR").unwrap();
    let wrong_domain = base_receipt
        .with_attestation(AttestationEnvelope {
            profile_id: SignatureProfileId::InkSigEd25519V1,
            issuer_id: base_receipt.issuer_id,
            public_key_id,
            signature: ink_core::Ed25519Signature(
                signing_key.sign(wrong_domain_hash.as_bytes()).to_bytes(),
            ),
            signed_message_hash: wrong_domain_hash,
            sequence: base_receipt.sequence,
            validity_window: None,
        })
        .unwrap();
    vectors.push(kernel_vector(
        "signature_from_wrong_domain_separator",
        wrong_domain,
        trusted_key_bytes.clone(),
        true,
        None,
        ReceiptStatus::SignatureInvalid,
        VerificationCode::SignedMessageHashMismatch,
        true,
    ));

    let expired_receipt = attest_receipt(
        base_receipt,
        SignatureProfileId::InkSigEd25519V1,
        public_key_id,
        &signing_key,
        Some(ValidityWindow::new(1, 5)),
    )
    .unwrap();
    vectors.push(kernel_vector(
        "expired_attestation",
        expired_receipt,
        trusted_key_bytes,
        true,
        Some(9),
        ReceiptStatus::SignatureExpired,
        VerificationCode::SignatureExpired,
        true,
    ));
    vectors
}

pub fn kernel_decode_vectors() -> Vec<KernelDecodeVector> {
    let valid = minimal_receipt_vector();
    let mut truncated = hex::decode(valid.canonical_bytes_hex).unwrap();
    truncated.pop();
    vec![
        KernelDecodeVector {
            name: "truncated_signature",
            receipt_bytes_hex: hex::encode(truncated),
            expected_error: "DECODE_ERROR",
        },
        KernelDecodeVector {
            name: "json_signed_artifact_rejected",
            receipt_bytes_hex: hex::encode(br#"{"schema":"ink.receipt.v2"}"#),
            expected_error: "DECODE_ERROR",
        },
    ]
}

fn seeded_signed_fixture() -> (ReceiptEnvelope, TrustedIssuerKey, SigningKey, PublicKeyId) {
    let schema = Schema::from_slice(
        SchemaId::from_str("ink.verify.v1").unwrap(),
        SchemaAuthority::from_str("ink").unwrap(),
        DomainTag::from_str("verify").unwrap(),
        1,
        b"{\"type\":\"object\"}",
    )
    .unwrap();
    let claim = Claim::from_slice(
        schema.id,
        SubjectId::from_str("subject-1").unwrap(),
        b"claim",
    )
    .unwrap();
    let evidence = Evidence::from_slice(schema.id, b"evidence").unwrap();
    let policy = Policy::from_slice(schema.id, PolicyDecision::Pass, b"policy").unwrap();
    let receipt = ReceiptEnvelope::create(
        schema.id,
        schema.compute_hash().unwrap(),
        schema.authority,
        schema.domain_tag,
        claim.compute_hash().unwrap(),
        IssuerId::from_str("issuer-1").unwrap(),
        7,
        claim.compute_hash().unwrap(),
        evidence.compute_hash().unwrap(),
        policy.compute_hash().unwrap(),
        Digest::new([5u8; 32]),
        ParentHashes::new(),
    )
    .seal()
    .unwrap();
    let signing_key = SigningKey::from_bytes(&[42u8; 32]);
    let public_key_id = PublicKeyId::from_str("issuer-key-1").unwrap();
    let trusted_key = TrustedIssuerKey {
        issuer_id: receipt.issuer_id,
        public_key_id,
        public_key: ink_core::Ed25519PublicKey(signing_key.verifying_key().to_bytes()),
    };
    (receipt, trusted_key, signing_key, public_key_id)
}

#[allow(clippy::too_many_arguments)]
fn kernel_vector(
    name: &'static str,
    receipt: ReceiptEnvelope,
    trusted_keys: Vec<TrustedIssuerKey>,
    allow_unsigned: bool,
    current_sequence: Option<u64>,
    expected_status: ReceiptStatus,
    expected_code: VerificationCode,
    expected_structural_valid: bool,
) -> KernelVerificationVector {
    let mut bytes = [0u8; 768];
    let len = canon::encode_receipt(&receipt, &mut bytes).unwrap();
    KernelVerificationVector {
        name,
        receipt_bytes_hex: hex::encode(&bytes[..len]),
        trusted_keys,
        allow_unsigned,
        current_sequence,
        expected_status,
        expected_code,
        expected_structural_valid,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ink_verify::VerificationPolicy;

    #[test]
    fn vector_receipt_verifies_and_is_stable() {
        let vector = minimal_receipt_vector();
        let bytes = hex::decode(&vector.canonical_bytes_hex).unwrap();
        let decoded = ink_core::canon::decode_receipt(&bytes).unwrap();
        let report =
            ink_verify::verify_receipt(&decoded, &[], ink_verify::VerificationPolicy::default())
                .unwrap();
        assert!(report.core.valid);
        assert_eq!(hex::encode(decoded.body_hash.0), vector.body_hash_hex);
    }

    #[test]
    fn verification_vectors_match_expected_statuses() {
        for vector in kernel_verification_vectors() {
            let bytes = hex::decode(&vector.receipt_bytes_hex).unwrap();
            let receipt = ink_core::canon::decode_receipt(&bytes).unwrap();
            let report = ink_verify::verify_receipt(
                &receipt,
                &vector.trusted_keys,
                VerificationPolicy {
                    allow_unsigned: vector.allow_unsigned,
                    current_sequence: vector.current_sequence,
                },
            )
            .unwrap();
            assert_eq!(report.status, vector.expected_status, "{}", vector.name);
            assert_eq!(report.code, vector.expected_code, "{}", vector.name);
            assert_eq!(
                report.core.valid, vector.expected_structural_valid,
                "{}",
                vector.name
            );
        }
    }
}
