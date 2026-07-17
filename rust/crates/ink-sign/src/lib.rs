#![forbid(unsafe_code)]
#![no_std]

use ed25519_dalek::{Signer, SigningKey};
use ink_core::bounded::PublicKeyId;
use ink_core::{
    canon, AttestationEnvelope, ReceiptEnvelope, SignatureBytes, SignatureProfileId, ValidityWindow,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SignError {
    Core(ink_core::Error),
}

impl From<ink_core::Error> for SignError {
    fn from(value: ink_core::Error) -> Self {
        Self::Core(value)
    }
}

pub trait ReceiptSigner {
    fn sign_message_hash(&self, message_hash: &ink_core::SignedMessageHash) -> SignatureBytes;
}

impl ReceiptSigner for SigningKey {
    fn sign_message_hash(&self, message_hash: &ink_core::SignedMessageHash) -> SignatureBytes {
        ink_core::Ed25519Signature(self.sign(message_hash.as_bytes()).to_bytes())
    }
}

pub fn build_attestation(
    receipt: &ReceiptEnvelope,
    profile_id: SignatureProfileId,
    public_key_id: PublicKeyId,
    signer: &impl ReceiptSigner,
    validity_window: Option<ValidityWindow>,
) -> Result<AttestationEnvelope, SignError> {
    let signed_message_hash = canon::compute_signed_message_hash(receipt, profile_id)?;
    Ok(AttestationEnvelope {
        profile_id,
        issuer_id: receipt.issuer_id,
        public_key_id,
        signature: signer.sign_message_hash(&signed_message_hash),
        signed_message_hash,
        sequence: receipt.sequence,
        validity_window,
    })
}

pub fn attest_receipt(
    receipt: ReceiptEnvelope,
    profile_id: SignatureProfileId,
    public_key_id: PublicKeyId,
    signer: &impl ReceiptSigner,
    validity_window: Option<ValidityWindow>,
) -> Result<ReceiptEnvelope, SignError> {
    let attestation =
        build_attestation(&receipt, profile_id, public_key_id, signer, validity_window)?;
    receipt
        .with_attestation(attestation)
        .map_err(SignError::from)
}
