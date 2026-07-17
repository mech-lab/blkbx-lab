use super::receipt::{receipt_transcript_hash, ReceiptPayload};
use crate::error::Error;
use crate::signing::verify_receipt_signature_for_digest;
use crate::types::{Ed25519PublicKey, Ed25519Signature, Sha256Digest};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum VerificationReason {
    Valid,
    InvalidSignature,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct VerificationOut {
    pub valid: bool,
    pub payload_hash: Sha256Digest,
    pub reason: VerificationReason,
}

pub fn verify_receipt(
    payload: &ReceiptPayload<'_>,
    signature: &Ed25519Signature,
    trusted_public_key: &Ed25519PublicKey,
    out: &mut VerificationOut,
) -> Result<(), Error> {
    let payload_hash = receipt_transcript_hash(payload)?;
    out.payload_hash = payload_hash;
    match verify_receipt_signature_for_digest(&payload_hash, signature, trusted_public_key) {
        Ok(()) => {
            out.valid = true;
            out.reason = VerificationReason::Valid;
        }
        Err(_) => {
            out.valid = false;
            out.reason = VerificationReason::InvalidSignature;
        }
    }
    Ok(())
}
