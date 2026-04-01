#![allow(dead_code)]

#[cfg(feature = "alloc")]
use alloc::vec::Vec;

/// Simple sparse vector (index-sorted) for early experiments.
#[derive(Clone, Debug, Default)]
pub struct SparseVec<T> {
    pub indices: Vec<u32>,
    pub values: Vec<T>,
}

impl<T> SparseVec<T> {
    pub fn new() -> Self {
        Self { indices: Vec::new(), values: Vec::new() }
    }

    pub fn push(&mut self, idx: u32, value: T) {
        self.indices.push(idx);
        self.values.push(value);
    }
}
