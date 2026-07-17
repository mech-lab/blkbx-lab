#![no_std]
#![forbid(unsafe_code)]

use ed25519_dalek::{Verifier, VerifyingKey};
use ink_core::bounded::{IssuerId, PublicKeyId};
use ink_core::{Bundle, Ed25519PublicKey, ReceiptEnvelope, SignatureBytes, SignatureProfileId};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum VerificationError {
    Core(ink_core::Error),
    InvalidTrustedKey,
}

impl From<ink_core::Error> for VerificationError {
    fn from(value: ink_core::Error) -> Self {
        Self::Core(value)
    }
}

pub type Result<T> = core::result::Result<T, VerificationError>;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ReceiptStatus {
    StructuralValidUnsigned,
    SignatureValid,
    SignatureInvalid,
    SignatureMissing,
    SignatureUnsupported,
    SignatureExpired,
    IssuerUnknown,
}

impl ReceiptStatus {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::StructuralValidUnsigned => "structural_valid_unsigned",
            Self::SignatureValid => "signature_valid",
            Self::SignatureInvalid => "signature_invalid",
            Self::SignatureMissing => "signature_missing",
            Self::SignatureUnsupported => "signature_unsupported",
            Self::SignatureExpired => "signature_expired",
            Self::IssuerUnknown => "issuer_unknown",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum VerificationCode {
    StructuralValidUnsigned,
    SignatureValid,
    SignatureMissing,
    SignatureUnsupported,
    SignatureExpired,
    IssuerUnknown,
    SignedMessageHashMismatch,
    InvalidSignature,
}

impl VerificationCode {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::StructuralValidUnsigned => "STRUCTURAL_VALID_UNSIGNED",
            Self::SignatureValid => "SIGNATURE_VALID",
            Self::SignatureMissing => "SIGNATURE_MISSING",
            Self::SignatureUnsupported => "SIGNATURE_UNSUPPORTED",
            Self::SignatureExpired => "SIGNATURE_EXPIRED",
            Self::IssuerUnknown => "ISSUER_UNKNOWN",
            Self::SignedMessageHashMismatch => "SIGNED_MESSAGE_HASH_MISMATCH",
            Self::InvalidSignature => "INVALID_SIGNATURE",
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TrustedIssuerKey {
    pub issuer_id: IssuerId,
    pub public_key_id: PublicKeyId,
    pub public_key: Ed25519PublicKey,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VerificationPolicy {
    pub allow_unsigned: bool,
    pub current_sequence: Option<u64>,
}

impl Default for VerificationPolicy {
    fn default() -> Self {
        Self {
            allow_unsigned: true,
            current_sequence: None,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ReceiptVerificationReport {
    pub core: ink_core::VerificationReport,
    pub status: ReceiptStatus,
    pub code: VerificationCode,
}

pub fn verify_ed25519_message_hash_bytes(
    signed_message_hash: &[u8; 32],
    signature: &[u8; 64],
    public_key: &[u8; 32],
) -> Result<bool> {
    let key =
        VerifyingKey::from_bytes(public_key).map_err(|_| VerificationError::InvalidTrustedKey)?;
    let signature = ed25519_dalek::Signature::from_bytes(signature);
    Ok(key.verify(signed_message_hash, &signature).is_ok())
}

pub fn verify_signed_message_hash(
    profile_id: SignatureProfileId,
    signed_message_hash: &ink_core::SignedMessageHash,
    signature: &SignatureBytes,
    public_key: &Ed25519PublicKey,
) -> Result<bool> {
    if !profile_id.is_supported() {
        return Ok(false);
    }
    verify_ed25519_message_hash_bytes(signed_message_hash.as_bytes(), &signature.0, &public_key.0)
}

pub fn verify_receipt(
    receipt: &ReceiptEnvelope,
    trusted_keys: &[TrustedIssuerKey],
    policy: VerificationPolicy,
) -> Result<ReceiptVerificationReport> {
    let core = ink_core::verify::verify_receipt(receipt)?;
    let Some(attestation) = receipt.attestation else {
        let (status, code) = if policy.allow_unsigned {
            (
                ReceiptStatus::StructuralValidUnsigned,
                VerificationCode::StructuralValidUnsigned,
            )
        } else {
            (
                ReceiptStatus::SignatureMissing,
                VerificationCode::SignatureMissing,
            )
        };
        return Ok(ReceiptVerificationReport { core, status, code });
    };

    if !attestation.profile_id.is_supported() {
        return Ok(ReceiptVerificationReport {
            core,
            status: ReceiptStatus::SignatureUnsupported,
            code: VerificationCode::SignatureUnsupported,
        });
    }

    if policy
        .current_sequence
        .zip(attestation.validity_window)
        .map(|(current_sequence, window)| !window.contains(current_sequence))
        .unwrap_or(false)
    {
        return Ok(ReceiptVerificationReport {
            core,
            status: ReceiptStatus::SignatureExpired,
            code: VerificationCode::SignatureExpired,
        });
    }

    let trusted_key = trusted_keys.iter().find(|candidate| {
        candidate.issuer_id == attestation.issuer_id
            && candidate.public_key_id == attestation.public_key_id
    });
    let Some(trusted_key) = trusted_key else {
        return Ok(ReceiptVerificationReport {
            core,
            status: ReceiptStatus::IssuerUnknown,
            code: VerificationCode::IssuerUnknown,
        });
    };

    let expected_hash =
        ink_core::canon::compute_signed_message_hash(receipt, attestation.profile_id)?;
    if attestation.signed_message_hash != expected_hash {
        return Ok(ReceiptVerificationReport {
            core,
            status: ReceiptStatus::SignatureInvalid,
            code: VerificationCode::SignedMessageHashMismatch,
        });
    }

    let signature_valid = verify_signed_message_hash(
        attestation.profile_id,
        &attestation.signed_message_hash,
        &attestation.signature,
        &trusted_key.public_key,
    )?;

    Ok(ReceiptVerificationReport {
        core,
        status: if signature_valid {
            ReceiptStatus::SignatureValid
        } else {
            ReceiptStatus::SignatureInvalid
        },
        code: if signature_valid {
            VerificationCode::SignatureValid
        } else {
            VerificationCode::InvalidSignature
        },
    })
}

pub fn verify_bundle(bundle: &Bundle) -> Result<ink_core::BundleVerificationReport> {
    ink_core::verify::verify_bundle(bundle).map_err(VerificationError::from)
}
