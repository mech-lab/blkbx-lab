use crate::{hash, Digest, Result, MAX_BUNDLE_SIZE};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Bundle {
    pub root_hash: Digest,
    receipt_hashes: [Digest; MAX_BUNDLE_SIZE],
    receipt_count: u8,
}

impl Bundle {
    pub const fn new() -> Self {
        Self {
            root_hash: Digest::zero(),
            receipt_hashes: [Digest::zero(); MAX_BUNDLE_SIZE],
            receipt_count: 0,
        }
    }

    pub fn add_receipt(&mut self, receipt_hash: Digest) -> Result<()> {
        if self.receipt_count as usize >= MAX_BUNDLE_SIZE {
            return Err(crate::Error::BundleTooLarge);
        }
        self.receipt_hashes[self.receipt_count as usize] = receipt_hash;
        self.receipt_count += 1;
        Ok(())
    }

    pub fn receipts(&self) -> &[Digest] {
        &self.receipt_hashes[..self.receipt_count as usize]
    }

    pub fn seal(mut self) -> Result<Self> {
        self.root_hash = self.compute_root()?;
        Ok(self)
    }

    pub fn compute_root(&self) -> Result<Digest> {
        let mut parts: [&[u8]; MAX_BUNDLE_SIZE] = [&[]; MAX_BUNDLE_SIZE];
        let mut index = 0usize;
        while index < self.receipt_count as usize {
            parts[index] = self.receipt_hashes[index].as_bytes();
            index += 1;
        }
        hash::hash_many_labeled(b"bundle", &parts[..self.receipt_count as usize])
    }
}

impl Default for Bundle {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BundleDiff {
    pub added_count: u8,
    pub removed_count: u8,
    pub reordered: bool,
}
