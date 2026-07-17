use sha2::{Digest as ShaDigest, Sha256};

use crate::{Digest, HashAlgorithm, Result};

pub const DEFAULT_HASH_ALGORITHM: HashAlgorithm = HashAlgorithm::Sha256;

pub fn hash_bytes(algorithm: HashAlgorithm, data: &[u8]) -> Result<Digest> {
    match algorithm {
        HashAlgorithm::Sha256 => {
            let mut hasher = Sha256::new();
            hasher.update(data);
            let result = hasher.finalize();
            let mut digest = [0u8; crate::DIGEST_SIZE];
            digest.copy_from_slice(&result);
            Ok(Digest(digest))
        }
    }
}

pub fn hash_labeled(label: &[u8], data: &[u8]) -> Result<Digest> {
    let label_len = (label.len() as u16).to_be_bytes();
    let data_len = (data.len() as u32).to_be_bytes();
    let parts = [&b"INK-V1"[..], &label_len[..], label, &data_len[..], data];
    hash_many_labeled(b"hash_labeled", &parts)
}

pub fn hash_many_labeled(label: &[u8], parts: &[&[u8]]) -> Result<Digest> {
    let mut hasher = Sha256::new();
    hasher.update(b"INK-V1");
    hasher.update((label.len() as u16).to_be_bytes());
    hasher.update(label);
    for part in parts {
        hasher.update((part.len() as u32).to_be_bytes());
        hasher.update(part);
    }
    let result = hasher.finalize();
    let mut digest = [0u8; crate::DIGEST_SIZE];
    digest.copy_from_slice(&result);
    Ok(Digest(digest))
}
