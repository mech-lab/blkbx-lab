use rayon::prelude::*;
use std::collections::HashMap;

use crate::error::Error;
use crate::types::Sha256Digest;

pub trait TranscriptSink {
    fn update(&mut self, bytes: &[u8]);
}

pub struct Sha256Sink(Sha256);

impl Sha256Sink {
    pub fn new() -> Self {
        Self(Sha256::new())
    }

    pub fn finalize(self) -> Sha256Digest {
        let bytes = self.0.finalize();
        let mut digest = [0u8; 32];
        digest.copy_from_slice(&bytes);
        Sha256Digest(digest)
    }
}

impl Default for Sha256Sink {
    fn default() -> Self {
        Self::new()
    }
}

impl TranscriptSink for Sha256Sink {
    fn update(&mut self, bytes: &[u8]) {
        self.0.update(bytes);
    }
}

pub fn sha256(bytes: &[u8]) -> Sha256Digest {
    let mut sink = Sha256Sink::new();
    sink.update(bytes);
    sink.finalize()
}

pub fn write_tlv(sink: &mut impl TranscriptSink, field_id: u16, value: &[u8]) -> Result<(), Error> {
    if value.len() > 1024 * 1024 {
        return Err(Error::TlvValueTooLarge);
    }
    sink.update(&field_id.to_be_bytes());
    sink.update(&(value.len() as u32).to_be_bytes());
    sink.update(value);
    Ok(())
}

pub fn write_u8_field(sink: &mut impl TranscriptSink, field_id: u16, value: u8) {
    write_tlv(sink, field_id, &[value]);
}

pub fn write_bool_field(sink: &mut impl TranscriptSink, field_id: u16, value: bool) {
    write_u8_field(sink, field_id, if value { 1 } else { 0 });
}

pub fn write_u32_field(sink: &mut impl TranscriptSink, field_id: u16, value: u32) {
    write_tlv(sink, field_id, &value.to_be_bytes());
}

pub fn write_i64_field(sink: &mut impl TranscriptSink, field_id: u16, value: i64) {
    write_tlv(sink, field_id, &value.to_be_bytes());
}

/// Parallel hashing for multiple inputs
pub fn parallel_sha256(bytes: &[&[u8]]) -> Vec<Sha256Digest> {
    bytes.par_iter().map(|data| sha256(data)).collect()
}

/// Hash cache with LRU eviction for frequently used hashes
pub struct HashCache {
    cache: HashMap<[u8; 32], Vec<u8>>, // digest -> original data
    max_size: usize,
    access_count: HashMap<[u8; 32], usize>,
}

impl HashCache {
    pub fn new(max_size: usize) -> Self {
        Self {
            cache: HashMap::with_capacity(max_size),
            max_size,
            access_count: HashMap::with_capacity(max_size),
        }
    }

    pub fn get(&mut self, data: &[u8]) -> Option<Sha256Digest> {
        let digest = sha256(data);
        let digest_bytes = digest.0;
        
        if let Some(count) = self.access_count.get_mut(&digest_bytes) {
            *count += 1;
            return Some(digest);
        }
        
        if self.cache.contains_key(&digest_bytes) {
            self.access_count.insert(digest_bytes, 1);
            return Some(digest);
        }
        
        None
    }

    pub fn insert(&mut self, data: &[u8]) -> Sha256Digest {
        let digest = sha256(data);
        let digest_bytes = digest.0;
        
        if self.cache.len() >= self.max_size {
            // Find least recently used entry
            if let Some((lru_digest, _)) = self.access_count
                .iter()
                .min_by_key(|(_, &count)| count)
                .map(|(digest, count)| (*digest, *count))
            {
                self.cache.remove(&lru_digest);
                self.access_count.remove(&lru_digest);
            }
        }
        
        self.cache.insert(digest_bytes, data.to_vec());
        self.access_count.insert(digest_bytes, 1);
        digest
    }

    pub fn clear(&mut self) {
        self.cache.clear();
        self.access_count.clear();
    }
}
