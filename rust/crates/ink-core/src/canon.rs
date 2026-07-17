use crate::bounded::{DomainTag, IssuerId, PublicKeyId, SchemaAuthority, SchemaId};
use crate::receipt::{AttestationEnvelope, ReceiptEnvelope, ValidityWindow};
use crate::{Digest, ParentHashes, Result, SignatureProfileId, SignedMessageHash};

const RECEIPT_MAGIC: &[u8; 4] = b"INKR";

pub fn encoded_receipt_len(receipt: &ReceiptEnvelope) -> usize {
    encoded_receipt_body_len(receipt)
        + 32
        + 1
        + receipt
            .attestation
            .map(encoded_attestation_len)
            .unwrap_or(0)
        + 1
        + receipt.sealed_hash.map(|_| 32).unwrap_or(0)
}

pub fn encode_receipt(receipt: &ReceiptEnvelope, out: &mut [u8]) -> Result<usize> {
    let required = encoded_receipt_len(receipt);
    if out.len() < required {
        return Err(crate::Error::BufferTooSmall);
    }
    let mut cursor = encode_receipt_body(receipt, out)?;
    cursor += write_digest(receipt.body_hash, &mut out[cursor..])?;
    cursor += write_attestation(receipt.attestation, &mut out[cursor..])?;
    cursor += write_optional_digest(receipt.sealed_hash, &mut out[cursor..])?;
    Ok(cursor)
}

pub fn encode_receipt_body(receipt: &ReceiptEnvelope, out: &mut [u8]) -> Result<usize> {
    let required = encoded_receipt_body_len(receipt);
    if out.len() < required {
        return Err(crate::Error::BufferTooSmall);
    }
    let mut cursor = 0usize;
    out[cursor..cursor + 4].copy_from_slice(RECEIPT_MAGIC);
    cursor += 4;
    out[cursor..cursor + 4].copy_from_slice(&receipt.version.to_be_bytes());
    cursor += 4;
    cursor += write_bounded(receipt.schema_id.as_bytes(), &mut out[cursor..])?;
    cursor += write_digest(receipt.schema_hash, &mut out[cursor..])?;
    cursor += write_bounded(receipt.schema_authority.as_bytes(), &mut out[cursor..])?;
    cursor += write_bounded(receipt.domain_tag.as_bytes(), &mut out[cursor..])?;
    cursor += write_digest(receipt.subject_hash, &mut out[cursor..])?;
    cursor += write_bounded(receipt.issuer_id.as_bytes(), &mut out[cursor..])?;
    out[cursor..cursor + 8].copy_from_slice(&receipt.sequence.to_be_bytes());
    cursor += 8;
    cursor += write_digest(receipt.claim_hash, &mut out[cursor..])?;
    cursor += write_digest(receipt.evidence_hash, &mut out[cursor..])?;
    cursor += write_digest(receipt.policy_hash, &mut out[cursor..])?;
    cursor += write_digest(receipt.trace_hash, &mut out[cursor..])?;
    cursor += write_parents(&receipt.parent_hashes, &mut out[cursor..])?;
    out[cursor] = receipt.lifecycle_state as u8;
    cursor += 1;
    Ok(cursor)
}

pub fn compute_receipt_body_hash(receipt: &ReceiptEnvelope) -> Result<Digest> {
    let mut buf = [0u8; 512];
    let len = encode_receipt_body(receipt, &mut buf)?;
    crate::hash::hash_bytes(crate::HashAlgorithm::Sha256, &buf[..len])
}

pub fn compute_signed_message_hash(
    receipt: &ReceiptEnvelope,
    profile_id: SignatureProfileId,
) -> Result<SignedMessageHash> {
    let mut buf = [0u8; 256];
    let len = encode_signed_message(receipt, profile_id, &mut buf)?;
    crate::hash::hash_bytes(crate::HashAlgorithm::Sha256, &buf[..len])
}

pub fn compute_sealed_receipt_hash(receipt: &ReceiptEnvelope) -> Result<Digest> {
    if receipt.attestation.is_none() {
        return Err(crate::Error::MissingSignature);
    }
    let mut buf = [0u8; 768];
    let mut cursor = encode_receipt_body(receipt, &mut buf)?;
    let body_hash = compute_receipt_body_hash(receipt)?;
    cursor += write_digest(body_hash, &mut buf[cursor..])?;
    cursor += write_attestation(receipt.attestation, &mut buf[cursor..])?;
    crate::hash::hash_bytes(crate::HashAlgorithm::Sha256, &buf[..cursor])
}

pub fn encode_signed_message(
    receipt: &ReceiptEnvelope,
    profile_id: SignatureProfileId,
    out: &mut [u8],
) -> Result<usize> {
    if !profile_id.is_supported() {
        return Err(crate::Error::UnsupportedSignatureProfile);
    }
    let issuer = receipt.issuer_id.as_bytes();
    let body_hash = compute_receipt_body_hash(receipt)?;
    let required = crate::SIGNING_DOMAIN_SEPARATOR.len()
        + 4
        + encoded_bounded_len(profile_id.as_bytes())
        + 32
        + 32
        + encoded_bounded_len(issuer)
        + 8;
    if out.len() < required {
        return Err(crate::Error::BufferTooSmall);
    }
    let mut cursor = 0usize;
    out[cursor..cursor + crate::SIGNING_DOMAIN_SEPARATOR.len()]
        .copy_from_slice(crate::SIGNING_DOMAIN_SEPARATOR);
    cursor += crate::SIGNING_DOMAIN_SEPARATOR.len();
    out[cursor..cursor + 4].copy_from_slice(&receipt.version.to_be_bytes());
    cursor += 4;
    cursor += write_bounded(profile_id.as_bytes(), &mut out[cursor..])?;
    out[cursor..cursor + 32].copy_from_slice(body_hash.as_bytes());
    cursor += 32;
    out[cursor..cursor + 32].copy_from_slice(receipt.schema_hash.as_bytes());
    cursor += 32;
    cursor += write_bounded(issuer, &mut out[cursor..])?;
    out[cursor..cursor + 8].copy_from_slice(&receipt.sequence.to_be_bytes());
    cursor += 8;
    Ok(cursor)
}

pub fn decode_receipt(bytes: &[u8]) -> Result<ReceiptEnvelope> {
    let mut cursor = 0usize;
    if bytes.len() < 4 || &bytes[..4] != RECEIPT_MAGIC {
        return Err(crate::Error::InvalidEncoding);
    }
    cursor += 4;
    let version = read_u32(bytes, &mut cursor)?;
    let schema_id = read_schema_id(bytes, &mut cursor)?;
    let schema_hash = read_digest(bytes, &mut cursor)?;
    let schema_authority = read_schema_authority(bytes, &mut cursor)?;
    let domain_tag = read_domain_tag(bytes, &mut cursor)?;
    let subject_hash = read_digest(bytes, &mut cursor)?;
    let issuer_id = read_issuer_id(bytes, &mut cursor)?;
    let sequence = read_u64(bytes, &mut cursor)?;
    let claim_hash = read_digest(bytes, &mut cursor)?;
    let evidence_hash = read_digest(bytes, &mut cursor)?;
    let policy_hash = read_digest(bytes, &mut cursor)?;
    let trace_hash = read_digest(bytes, &mut cursor)?;
    let parent_hashes = read_parents(bytes, &mut cursor)?;
    let lifecycle_state = crate::lifecycle::LifecycleState::from_u8(read_u8(bytes, &mut cursor)?)
        .ok_or(crate::Error::InvalidLifecycleState)?;
    let body_hash = read_digest(bytes, &mut cursor)?;
    let attestation = read_attestation(bytes, &mut cursor)?;
    let sealed_hash = read_optional_digest(bytes, &mut cursor)?;
    Ok(ReceiptEnvelope {
        version,
        schema_id,
        schema_hash,
        schema_authority,
        domain_tag,
        subject_hash,
        issuer_id,
        sequence,
        claim_hash,
        evidence_hash,
        policy_hash,
        trace_hash,
        parent_hashes,
        lifecycle_state,
        body_hash,
        sealed_hash,
        attestation,
    })
}

fn encoded_receipt_body_len(receipt: &ReceiptEnvelope) -> usize {
    4 + 4
        + encoded_bounded_len(receipt.schema_id.as_bytes())
        + 32
        + encoded_bounded_len(receipt.schema_authority.as_bytes())
        + encoded_bounded_len(receipt.domain_tag.as_bytes())
        + 32
        + encoded_bounded_len(receipt.issuer_id.as_bytes())
        + 8
        + 32
        + 32
        + 32
        + 32
        + 1
        + (receipt.parent_hashes.len() * 32)
        + 1
}

fn encoded_bounded_len(bytes: &[u8]) -> usize {
    1 + bytes.len()
}

fn encoded_attestation_len(attestation: AttestationEnvelope) -> usize {
    1 + encoded_bounded_len(attestation.issuer_id.as_bytes())
        + encoded_bounded_len(attestation.public_key_id.as_bytes())
        + 32
        + 8
        + 1
        + attestation.validity_window.map(|_| 16).unwrap_or(0)
        + 64
}

fn write_bounded(bytes: &[u8], out: &mut [u8]) -> Result<usize> {
    if bytes.len() > u8::MAX as usize || out.len() < encoded_bounded_len(bytes) {
        return Err(crate::Error::BufferTooSmall);
    }
    out[0] = bytes.len() as u8;
    out[1..1 + bytes.len()].copy_from_slice(bytes);
    Ok(1 + bytes.len())
}

fn write_digest(digest: Digest, out: &mut [u8]) -> Result<usize> {
    if out.len() < 32 {
        return Err(crate::Error::BufferTooSmall);
    }
    out[..32].copy_from_slice(digest.as_bytes());
    Ok(32)
}

fn write_optional_digest(digest: Option<Digest>, out: &mut [u8]) -> Result<usize> {
    if out.is_empty() {
        return Err(crate::Error::BufferTooSmall);
    }
    match digest {
        Some(value) => {
            if out.len() < 33 {
                return Err(crate::Error::BufferTooSmall);
            }
            out[0] = 1;
            write_digest(value, &mut out[1..])?;
            Ok(33)
        }
        None => {
            out[0] = 0;
            Ok(1)
        }
    }
}

fn write_parents(parents: &ParentHashes, out: &mut [u8]) -> Result<usize> {
    let needed = 1 + (parents.len() * 32);
    if out.len() < needed {
        return Err(crate::Error::BufferTooSmall);
    }
    out[0] = parents.len() as u8;
    let mut cursor = 1usize;
    for parent in parents.as_slice() {
        out[cursor..cursor + 32].copy_from_slice(parent.as_bytes());
        cursor += 32;
    }
    Ok(cursor)
}

fn write_attestation(attestation: Option<AttestationEnvelope>, out: &mut [u8]) -> Result<usize> {
    if out.is_empty() {
        return Err(crate::Error::BufferTooSmall);
    }
    match attestation {
        None => {
            out[0] = 0;
            Ok(1)
        }
        Some(attestation) => {
            let needed = 1 + encoded_attestation_len(attestation);
            if out.len() < needed {
                return Err(crate::Error::BufferTooSmall);
            }
            out[0] = 1;
            let mut cursor = 1usize;
            out[cursor] = attestation.profile_id.as_u8();
            cursor += 1;
            cursor += write_bounded(attestation.issuer_id.as_bytes(), &mut out[cursor..])?;
            cursor += write_bounded(attestation.public_key_id.as_bytes(), &mut out[cursor..])?;
            out[cursor..cursor + 32].copy_from_slice(attestation.signed_message_hash.as_bytes());
            cursor += 32;
            out[cursor..cursor + 8].copy_from_slice(&attestation.sequence.to_be_bytes());
            cursor += 8;
            match attestation.validity_window {
                Some(window) => {
                    out[cursor] = 1;
                    cursor += 1;
                    out[cursor..cursor + 8]
                        .copy_from_slice(&window.not_before_sequence.to_be_bytes());
                    cursor += 8;
                    out[cursor..cursor + 8]
                        .copy_from_slice(&window.not_after_sequence.to_be_bytes());
                    cursor += 8;
                }
                None => {
                    out[cursor] = 0;
                    cursor += 1;
                }
            }
            out[cursor..cursor + 64].copy_from_slice(&attestation.signature.0);
            cursor += 64;
            Ok(cursor)
        }
    }
}

fn read_u8(bytes: &[u8], cursor: &mut usize) -> Result<u8> {
    if *cursor >= bytes.len() {
        return Err(crate::Error::TruncatedInput);
    }
    let value = bytes[*cursor];
    *cursor += 1;
    Ok(value)
}

fn read_u32(bytes: &[u8], cursor: &mut usize) -> Result<u32> {
    if bytes.len().saturating_sub(*cursor) < 4 {
        return Err(crate::Error::TruncatedInput);
    }
    let mut raw = [0u8; 4];
    raw.copy_from_slice(&bytes[*cursor..*cursor + 4]);
    *cursor += 4;
    Ok(u32::from_be_bytes(raw))
}

fn read_u64(bytes: &[u8], cursor: &mut usize) -> Result<u64> {
    if bytes.len().saturating_sub(*cursor) < 8 {
        return Err(crate::Error::TruncatedInput);
    }
    let mut raw = [0u8; 8];
    raw.copy_from_slice(&bytes[*cursor..*cursor + 8]);
    *cursor += 8;
    Ok(u64::from_be_bytes(raw))
}

fn read_digest(bytes: &[u8], cursor: &mut usize) -> Result<Digest> {
    if bytes.len().saturating_sub(*cursor) < 32 {
        return Err(crate::Error::TruncatedInput);
    }
    let mut raw = [0u8; 32];
    raw.copy_from_slice(&bytes[*cursor..*cursor + 32]);
    *cursor += 32;
    Ok(Digest(raw))
}

fn read_optional_digest(bytes: &[u8], cursor: &mut usize) -> Result<Option<Digest>> {
    match read_u8(bytes, cursor)? {
        0 => Ok(None),
        1 => Ok(Some(read_digest(bytes, cursor)?)),
        _ => Err(crate::Error::InvalidEncoding),
    }
}

fn read_bounded<'a>(bytes: &'a [u8], cursor: &mut usize) -> Result<&'a [u8]> {
    let len = read_u8(bytes, cursor)? as usize;
    if bytes.len().saturating_sub(*cursor) < len {
        return Err(crate::Error::TruncatedInput);
    }
    let slice = &bytes[*cursor..*cursor + len];
    *cursor += len;
    Ok(slice)
}

fn read_schema_id(bytes: &[u8], cursor: &mut usize) -> Result<SchemaId> {
    SchemaId::from_bytes(read_bounded(bytes, cursor)?)
}

fn read_schema_authority(bytes: &[u8], cursor: &mut usize) -> Result<SchemaAuthority> {
    SchemaAuthority::from_bytes(read_bounded(bytes, cursor)?)
}

fn read_domain_tag(bytes: &[u8], cursor: &mut usize) -> Result<DomainTag> {
    DomainTag::from_bytes(read_bounded(bytes, cursor)?)
}

fn read_issuer_id(bytes: &[u8], cursor: &mut usize) -> Result<IssuerId> {
    IssuerId::from_bytes(read_bounded(bytes, cursor)?)
}

fn read_public_key_id(bytes: &[u8], cursor: &mut usize) -> Result<PublicKeyId> {
    PublicKeyId::from_bytes(read_bounded(bytes, cursor)?)
}

fn read_parents(bytes: &[u8], cursor: &mut usize) -> Result<ParentHashes> {
    let count = read_u8(bytes, cursor)? as usize;
    if count > crate::MAX_PARENT_HASHES {
        return Err(crate::Error::TooManyParents);
    }
    let mut parents = ParentHashes::new();
    let mut index = 0usize;
    while index < count {
        parents.push(read_digest(bytes, cursor)?)?;
        index += 1;
    }
    Ok(parents)
}

fn read_attestation(bytes: &[u8], cursor: &mut usize) -> Result<Option<AttestationEnvelope>> {
    let present = read_u8(bytes, cursor)?;
    if present == 0 {
        return Ok(None);
    }
    let profile_id = SignatureProfileId::from_u8(read_u8(bytes, cursor)?);
    let issuer_id = read_issuer_id(bytes, cursor)?;
    let public_key_id = read_public_key_id(bytes, cursor)?;
    let signed_message_hash = read_digest(bytes, cursor)?;
    let sequence = read_u64(bytes, cursor)?;
    let validity_window = match read_u8(bytes, cursor)? {
        0 => None,
        1 => Some(ValidityWindow::new(
            read_u64(bytes, cursor)?,
            read_u64(bytes, cursor)?,
        )),
        _ => return Err(crate::Error::InvalidEncoding),
    };
    if bytes.len().saturating_sub(*cursor) < 64 {
        return Err(crate::Error::TruncatedInput);
    }
    let mut signature = [0u8; 64];
    signature.copy_from_slice(&bytes[*cursor..*cursor + 64]);
    *cursor += 64;
    Ok(Some(AttestationEnvelope {
        profile_id,
        issuer_id,
        public_key_id,
        signature: crate::Ed25519Signature(signature),
        signed_message_hash,
        sequence,
        validity_window,
    }))
}
