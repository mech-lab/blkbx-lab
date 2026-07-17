use crate::bounded::{DomainTag, IssuerId, PublicKeyId, SchemaAuthority, SchemaId, SubjectId};
use crate::{
    canon, Claim, Digest, Evidence, ParentHashes, Policy, PolicyDecision, ReceiptEnvelope, Schema,
    SignatureProfileId, ValidityWindow,
};

fn sample_receipt() -> ReceiptEnvelope {
    let schema = Schema::from_slice(
        SchemaId::from_str("ink.test.v1").unwrap(),
        SchemaAuthority::from_str("ink").unwrap(),
        DomainTag::from_str("test").unwrap(),
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
    ReceiptEnvelope::create(
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
        Digest::new([7u8; 32]),
        ParentHashes::new(),
    )
    .seal()
    .unwrap()
}

#[test]
fn unsigned_receipt_round_trips_with_body_hash() {
    let receipt = sample_receipt();
    let mut bytes = [0u8; 512];
    let len = canon::encode_receipt(&receipt, &mut bytes).unwrap();
    let decoded = canon::decode_receipt(&bytes[..len]).unwrap();
    assert_eq!(decoded.body_hash, receipt.body_hash);
    assert_eq!(decoded.sealed_hash, None);
    let report = crate::verify::verify_receipt(&decoded).unwrap();
    assert!(report.valid);
    assert!(report.body_hash_valid);
    assert!(report.sealed_hash_valid);
}

#[test]
fn attestation_changes_sealed_hash_but_not_body_hash() {
    let receipt = sample_receipt();
    let signed_message_hash =
        canon::compute_signed_message_hash(&receipt, SignatureProfileId::InkSigEd25519V1).unwrap();
    let attested = receipt
        .with_attestation(crate::AttestationEnvelope {
            profile_id: SignatureProfileId::InkSigEd25519V1,
            issuer_id: receipt.issuer_id,
            public_key_id: PublicKeyId::from_str("issuer-key-1").unwrap(),
            signature: crate::SignatureBytes::new([3u8; 64]),
            signed_message_hash,
            sequence: receipt.sequence,
            validity_window: Some(ValidityWindow::new(1, 10)),
        })
        .unwrap();
    assert_eq!(attested.body_hash, receipt.body_hash);
    assert_ne!(attested.sealed_hash, None);
    assert_ne!(attested.sealed_hash, Some(attested.body_hash));
    let report = crate::verify::verify_receipt(&attested).unwrap();
    assert!(report.valid);
    assert!(report.sealed_hash_valid);
}

#[test]
fn signed_message_hash_is_stable_for_same_body() {
    let receipt = sample_receipt();
    let first =
        canon::compute_signed_message_hash(&receipt, SignatureProfileId::InkSigEd25519V1).unwrap();
    let second =
        canon::compute_signed_message_hash(&receipt, SignatureProfileId::InkSigEd25519V1).unwrap();
    assert_eq!(first, second);
}
