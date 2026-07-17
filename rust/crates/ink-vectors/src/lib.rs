#![forbid(unsafe_code)]

use ink_core::bounded::{DomainTag, IssuerId, SchemaAuthority, SchemaId, SubjectId};
use ink_core::{
    canon, Claim, Digest, Evidence, ParentHashes, Policy, PolicyDecision, ReceiptEnvelope, Schema,
};

pub const PUBLIC_RECEIPT_VECTORS_JSON: &str =
    include_str!("../../../../test-vectors/ink-vectors.json");

pub struct ReceiptVector {
    pub name: &'static str,
    pub human_fixture: &'static str,
    pub canonical_bytes_hex: String,
    pub canonical_hash_hex: String,
    pub schema_hash_hex: String,
    pub evidence_hash_hex: String,
    pub expected_verify: bool,
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
        canonical_hash_hex: hex::encode(receipt.canonical_hash.0),
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn vector_receipt_verifies_and_is_stable() {
        let vector = minimal_receipt_vector();
        let bytes = hex::decode(&vector.canonical_bytes_hex).unwrap();
        let decoded = ink_core::canon::decode_receipt(&bytes).unwrap();
        let report = ink_verify::verify_receipt(&decoded).unwrap();
        assert!(report.core.valid);
        assert_eq!(
            hex::encode(decoded.canonical_hash.0),
            vector.canonical_hash_hex
        );
    }
}
