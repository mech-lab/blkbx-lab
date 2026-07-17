use crate::bounded::{DomainTag, IssuerId, SchemaAuthority, SchemaId};
use crate::receipt::AttestationRef;
use crate::{Digest, ParentHashes, ReceiptEnvelope, Result};

const RECEIPT_MAGIC: &[u8; 4] = b"INKR";
const SIGNING_DOMAIN: &[u8; 9] = b"INK-SIG1\0";

pub fn encoded_receipt_len(receipt: &ReceiptEnvelope) -> usize {
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
        + 32
        + 1
        + receipt.attestation.map(|_| 1 + 32 + 64).unwrap_or(0)
}

pub fn encode_receipt(receipt: &ReceiptEnvelope, out: &mut [u8]) -> Result<usize> {
    encode_receipt_inner(receipt, out)
}

pub fn compute_receipt_hash(receipt: &ReceiptEnvelope) -> Result<Digest> {
    let mut copy = *receipt;
    copy.canonical_hash = Digest::zero();
    let mut buf = [0u8; 512];
    let len = encode_receipt_inner(&copy, &mut buf)?;
    crate::hash::hash_bytes(crate::HashAlgorithm::Sha256, &buf[..len])
}

pub fn encode_signed_message(
    receipt: &ReceiptEnvelope,
    algorithm: crate::SignatureAlgorithm,
    out: &mut [u8],
) -> Result<usize> {
    let issuer = receipt.issuer_id.as_bytes();
    let required = SIGNING_DOMAIN.len() + 1 + 4 + 32 + 32 + encoded_bounded_len(issuer);
    if out.len() < required {
        return Err(crate::Error::BufferTooSmall);
    }
    let mut cursor = 0usize;
    out[cursor..cursor + SIGNING_DOMAIN.len()].copy_from_slice(SIGNING_DOMAIN);
    cursor += SIGNING_DOMAIN.len();
    out[cursor] = algorithm as u8;
    cursor += 1;
    out[cursor..cursor + 4].copy_from_slice(&receipt.version.to_be_bytes());
    cursor += 4;
    out[cursor..cursor + 32].copy_from_slice(receipt.canonical_hash.as_bytes());
    cursor += 32;
    out[cursor..cursor + 32].copy_from_slice(receipt.schema_hash.as_bytes());
    cursor += 32;
    cursor += write_bounded(issuer, &mut out[cursor..])?;
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
    let canonical_hash = read_digest(bytes, &mut cursor)?;
    let attestation = read_attestation(bytes, &mut cursor)?;
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
        canonical_hash,
        attestation,
    })
}

fn encode_receipt_inner(receipt: &ReceiptEnvelope, out: &mut [u8]) -> Result<usize> {
    let required = encoded_receipt_len(receipt);
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
    cursor += write_digest(receipt.canonical_hash, &mut out[cursor..])?;
    cursor += write_attestation(receipt.attestation, &mut out[cursor..])?;
    Ok(cursor)
}

fn encoded_bounded_len(bytes: &[u8]) -> usize {
    1 + bytes.len()
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

fn write_attestation(attestation: Option<AttestationRef>, out: &mut [u8]) -> Result<usize> {
    if out.is_empty() {
        return Err(crate::Error::BufferTooSmall);
    }
    match attestation {
        None => {
            out[0] = 0;
            Ok(1)
        }
        Some(attestation) => {
            if out.len() < 98 {
                return Err(crate::Error::BufferTooSmall);
            }
            out[0] = 1;
            out[1] = attestation.algorithm as u8;
            out[2..34].copy_from_slice(&attestation.public_key.0);
            out[34..98].copy_from_slice(&attestation.signature.0);
            Ok(98)
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

fn read_attestation(bytes: &[u8], cursor: &mut usize) -> Result<Option<AttestationRef>> {
    let present = read_u8(bytes, cursor)?;
    if present == 0 {
        return Ok(None);
    }
    let algorithm = crate::SignatureAlgorithm::from_u8(read_u8(bytes, cursor)?)
        .ok_or(crate::Error::UnsupportedSignatureAlgorithm)?;
    if bytes.len().saturating_sub(*cursor) < 96 {
        return Err(crate::Error::TruncatedInput);
    }
    let mut public_key = [0u8; 32];
    public_key.copy_from_slice(&bytes[*cursor..*cursor + 32]);
    *cursor += 32;
    let mut signature = [0u8; 64];
    signature.copy_from_slice(&bytes[*cursor..*cursor + 64]);
    *cursor += 64;
    Ok(Some(AttestationRef {
        algorithm,
        public_key: crate::Ed25519PublicKey(public_key),
        signature: crate::Ed25519Signature(signature),
    }))
}
