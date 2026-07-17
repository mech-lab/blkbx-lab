#![no_std]
#![forbid(unsafe_code)]

use ed25519_dalek::{Verifier, VerifyingKey};
use ink_core::canon::encode_signed_message;
use ink_core::{Bundle, ReceiptEnvelope};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AttestationStatus {
    NotPresent,
    Valid,
    InvalidSignature,
    UnsupportedAlgorithm,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ReceiptVerificationReport {
    pub core: ink_core::VerificationReport,
    pub attestation: AttestationStatus,
}

pub fn verify_attestation(receipt: &ReceiptEnvelope) -> ink_core::Result<AttestationStatus> {
    let Some(attestation) = receipt.attestation else {
        return Ok(AttestationStatus::NotPresent);
    };
    match attestation.algorithm {
        ink_core::SignatureAlgorithm::Ed25519 => {
            let mut buf = [0u8; 256];
            let len = encode_signed_message(receipt, attestation.algorithm, &mut buf)?;
            let key = VerifyingKey::from_bytes(&attestation.public_key.0)
                .map_err(|_| ink_core::Error::SignatureVerificationFailed)?;
            let signature = ed25519_dalek::Signature::from_bytes(&attestation.signature.0);
            if key.verify(&buf[..len], &signature).is_ok() {
                Ok(AttestationStatus::Valid)
            } else {
                Ok(AttestationStatus::InvalidSignature)
            }
        }
    }
}

pub fn verify_receipt(receipt: &ReceiptEnvelope) -> ink_core::Result<ReceiptVerificationReport> {
    let core = ink_core::verify::verify_receipt(receipt)?;
    let attestation = verify_attestation(receipt)?;
    Ok(ReceiptVerificationReport { core, attestation })
}

pub fn verify_bundle(bundle: &Bundle) -> ink_core::Result<ink_core::BundleVerificationReport> {
    ink_core::verify::verify_bundle(bundle)
}

#[cfg(test)]
mod tests {
    use crate::{verify_receipt, AttestationStatus};
    use ink_core::bounded::{DomainTag, IssuerId, SchemaAuthority, SchemaId, SubjectId};
    use ink_core::{
        Claim, Digest, Evidence, ParentHashes, Policy, PolicyDecision, ReceiptEnvelope, Schema,
    };

    #[test]
    fn hash_only_receipt_is_still_valid() {
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
        let trace_hash = Digest::new([7u8; 32]);
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
            trace_hash,
            ParentHashes::new(),
        )
        .seal()
        .unwrap();

        let report = verify_receipt(&receipt).unwrap();
        assert!(report.core.valid);
        assert_eq!(report.attestation, AttestationStatus::NotPresent);
    }
}
