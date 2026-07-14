//! Hashing optimization module for improved performance.
//!
//! This module provides optimized hashing implementations including:
//! - Parallel hashing with Rayon
//! - Hash caching with LRU eviction
//! - Batch processing for multiple inputs
//! - Streaming hashing for large inputs

use rayon::prelude::*;
use std::collections::HashMap;

use crate::error::Error;
use crate::types::Sha256Digest;

/// Parallel hasher that processes multiple inputs concurrently
pub struct ParallelHasher {
    thread_pool: rayon::ThreadPool,
}

impl ParallelHasher {
    /// Create a new parallel hasher with optimal thread count
    pub fn new() -> Self {
        let thread_pool = rayon::ThreadPoolBuilder::new()
            .num_threads(num_cpus::get())
            .build()
            .expect("Failed to build thread pool");
        Self { thread_pool }
    }

    /// Hash multiple inputs in parallel
    pub fn hash_batch(&self, inputs: &[&[u8]]) -> Vec<Sha256Digest> {
        self.thread_pool.install(|| {
            inputs.par_iter()
                .map(|data| sha256(data))
                .collect()
        })
    }

    /// Hash a single input using the thread pool
    pub fn hash(&self, data: &[u8]) -> Sha256Digest {
        self.thread_pool.install(|| sha256(data))
    }
}

/// Hash cache with LRU eviction policy
pub struct HashCache {
    cache: HashMap<[u8; 32], CachedEntry>,
    max_size: usize,
    access_order: Vec<[u8; 32]>, // For LRU tracking
}

struct CachedEntry {
    data: Vec<u8>,
    access_count: usize,
    last_access: u64, // Timestamp for LRU
}

impl HashCache {
    /// Create a new hash cache with specified maximum size
    pub fn new(max_size: usize) -> Self {
        Self {
            cache: HashMap::with_capacity(max_size),
            max_size,
            access_order: Vec::with_capacity(max_size),
        }
    }

    /// Get a hash from cache, computing if not present
    pub fn get_or_compute<F>(&mut self, data: &[u8], compute: F) -> Sha256Digest
    where
        F: FnOnce(&[u8]) -> Sha256Digest,
    {
        let digest = sha256(data);
        let digest_bytes = digest.0;

        // Check if already cached
        if let Some(entry) = self.cache.get_mut(&digest_bytes) {
            entry.access_count += 1;
            entry.last_access = self.get_timestamp();
            return digest;
        }

        // Compute and cache if not present
        let result = compute(data);
        
        // Evict if cache is full
        if self.cache.len() >= self.max_size {
            self.evict_lru();
        }

        self.cache.insert(digest_bytes, CachedEntry {
            data: data.to_vec(),
            access_count: 1,
            last_access: self.get_timestamp(),
        });
        self.access_order.push(digest_bytes);

        result
    }

    /// Get a hash from cache without computing
    pub fn get(&self, data: &[u8]) -> Option<Sha256Digest> {
        let digest = sha256(data);
        let digest_bytes = digest.0;
        
        self.cache.get(&digest_bytes).map(|_| digest)
    }

    /// Insert a hash into cache
    pub fn insert(&mut self, data: &[u8]) -> Sha256Digest {
        let digest = sha256(data);
        let digest_bytes = digest.0;

        if self.cache.len() >= self.max_size {
            self.evict_lru();
        }

        self.cache.insert(digest_bytes, CachedEntry {
            data: data.to_vec(),
            access_count: 1,
            last_access: self.get_timestamp(),
        });
        self.access_order.push(digest_bytes);

        digest
    }

    /// Clear the cache
    pub fn clear(&mut self) {
        self.cache.clear();
        self.access_order.clear();
    }

    fn evict_lru(&mut self) {
        if let Some(lru_key) = self.access_order.first().cloned() {
            self.cache.remove(&lru_key);
            self.access_order.remove(0);
        }
    }

    fn get_timestamp(&self) -> u64 {
        // Simple timestamp - in production, use std::time::Instant
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64
    }
}

/// Batch hasher for processing large numbers of inputs efficiently
pub struct BatchHasher {
    chunk_size: usize,
    parallel: bool,
}

impl BatchHasher {
    /// Create a new batch hasher
    pub fn new(chunk_size: usize, parallel: bool) -> Self {
        Self { chunk_size, parallel }
    }

    /// Hash a batch of inputs
    pub fn hash_batch(&self, inputs: &[&[u8]]) -> Vec<Sha256Digest> {
        if self.parallel {
            self.hash_parallel(inputs)
        } else {
            self.hash_sequential(inputs)
        }
    }

    fn hash_parallel(&self, inputs: &[&[u8]]) -> Vec<Sha256Digest> {
        inputs
            .par_chunks(self.chunk_size)
            .flat_map(|chunk| chunk.iter().map(|data| sha256(data)))
            .collect()
    }

    fn hash_sequential(&self, inputs: &[&[u8]]) -> Vec<Sha256Digest> {
        inputs.iter().map(|data| sha256(data)).collect()
    }
}

/// Streaming hasher for large inputs
pub struct StreamingHasher {
    buffer: Vec<u8>,
    hasher: Sha256,
}

impl StreamingHasher {
    /// Create a new streaming hasher
    pub fn new() -> Self {
        Self {
            buffer: Vec::new(),
            hasher: Sha256::new(),
        }
    }

    /// Update the hasher with more data
    pub fn update(&mut self, data: &[u8]) {
        self.hasher.update(data);
        self.buffer.extend_from_slice(data);
    }

    /// Finalize the hash
    pub fn finalize(self) -> Sha256Digest {
        let bytes = self.hasher.finalize();
        let mut digest = [0u8; 32];
        digest.copy_from_slice(&bytes);
        Sha256Digest(digest)
    }

    /// Get the current hash without finalizing
    pub fn current_hash(&self) -> Sha256Digest {
        let bytes = self.hasher.clone().finalize();
        let mut digest = [0u8; 32];
        digest.copy_from_slice(&bytes);
        Sha256Digest(digest)
    }

    /// Reset the hasher
    pub fn reset(&mut self) {
        self.buffer.clear();
        self.hasher = Sha256::new();
    }
}

/// Optimized hash function with caching support
pub fn optimized_hash(data: &[u8], cache: &mut Option<HashCache>) -> Sha256Digest {
    match cache {
        Some(cache) => cache.get_or_compute(data, |d| sha256(d)),
        None => sha256(data),
    }
}

/// Batch hash function with optional caching
pub fn batch_hash(inputs: &[&[u8]], cache: &mut Option<HashCache>) -> Vec<Sha256Digest> {
    if let Some(cache) = cache {
        inputs.iter().map(|data| optimized_hash(data, cache)).collect()
    } else {
        inputs.iter().map(|data| sha256(data)).collect()
    }
}

/// Hash comparison function for testing
pub fn compare_hash_performance<F>(data: &[&[u8]], hasher: F) -> f64
where
    F: Fn(&[&[u8]]) -> Vec<Sha256Digest>,
{
    use std::time::Instant;
    
    let start = Instant::now();
    let _results = hasher(data);
    let duration = start.elapsed();
    
    duration.as_nanos() as f64
}