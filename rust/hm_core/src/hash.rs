#![allow(dead_code)]

use core::hash::{Hash, Hasher};

/// Tiny deterministic helper (FNV-1a 64) for IDs/codecs.
pub fn hash64<T: Hash>(value: &T) -> u64 {
    let mut h = fnv::FnvHasher::default();
    value.hash(&mut h);
    h.finish()
}

mod fnv {
    use core::hash::Hasher;

    pub struct FnvHasher(u64);

    impl Default for FnvHasher {
        fn default() -> Self {
            Self(0xcbf29ce484222325)
        }
    }

    impl Hasher for FnvHasher {
        fn write(&mut self, bytes: &[u8]) {
            for b in bytes {
                self.0 ^= *b as u64;
                self.0 = self.0.wrapping_mul(0x100000001b3);
            }
        }

        fn finish(&self) -> u64 {
            self.0
        }
    }
}
