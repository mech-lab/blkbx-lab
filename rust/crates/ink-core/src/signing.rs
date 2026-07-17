use ed25519_dalek::{Signer, SigningKey, Verifier, VerifyingKey};

use crate::error::Error;
use crate::legacy::receipt::{receipt_transcript_hash, ReceiptPayload};
use crate::types::{Ed25519PublicKey, Ed25519Signature};

pub trait ReceiptSigner {
    fn sign_digest(&self, digest: &[u8; 32]) -> Result<Ed25519Signature, Error>;
}

impl ReceiptSigner for SigningKey {
    fn sign_digest(&self, digest: &[u8; 32]) -> Result<Ed25519Signature, Error> {
        let signature = self.sign(digest);
        Ok(Ed25519Signature(signature.to_bytes()))
    }
}

pub fn sign_receipt_payload(
    payload: &ReceiptPayload<'_>,
    signer: &impl ReceiptSigner,
) -> Result<Ed25519Signature, Error> {
    let digest = receipt_transcript_hash(payload)?;
    signer.sign_digest(&digest.0)
}

pub fn verify_receipt_signature(
    payload: &ReceiptPayload<'_>,
    signature: &Ed25519Signature,
    public_key: &Ed25519PublicKey,
) -> Result<(), Error> {
    let digest = receipt_transcript_hash(payload)?;
    verify_receipt_signature_for_digest(&digest, signature, public_key)
}

pub fn verify_receipt_signature_for_digest(
    digest: &crate::types::Sha256Digest,
    signature: &Ed25519Signature,
    public_key: &Ed25519PublicKey,
) -> Result<(), Error> {
    let verifying_key =
        VerifyingKey::from_bytes(&public_key.0).map_err(|_| Error::SignatureError)?;
    let signature = ed25519_dalek::Signature::from_bytes(&signature.0);
    verifying_key
        .verify(&digest.0, &signature)
        .map_err(|_| Error::SignatureError)
}
