//! INK Receipts v1 kernel.
//!
//! The public kernel is domain-neutral and no_std. Product-specific receipt
//! vocabularies stay above this layer.

#![no_std]
#![forbid(unsafe_code)]

pub mod bundle;
pub mod canon;
pub mod claim;
pub mod compare;
pub mod controls;
pub mod digest;
pub mod domain;
pub mod error;
pub mod event;
pub mod evidence;
pub mod field_ids;
pub mod hash;
pub mod legacy;
pub mod lifecycle;
pub mod limits;
pub mod manifest;
pub mod model_waist;
pub mod policy;
pub mod receipt;
pub mod replay;
pub mod schema;
pub mod signing;
pub mod types;
pub mod verify;

pub use bundle::{Bundle, BundleDiff};
pub use claim::{Claim, ClaimCommitment};
pub use compare::{CompareReport, DiffKind, ReceiptDiff};
pub use error::{Error, Result};
pub use event::{TraceEvent, TraceEventType};
pub use evidence::{Evidence, EvidenceCommitment};
pub use lifecycle::{is_valid_transition, LifecycleState};
pub use policy::{Policy, PolicyCommitment, PolicyDecision};
pub use receipt::{AttestationRef, ReceiptEnvelope};
pub use replay::ReplayReport;
pub use schema::{Schema, SchemaCommitment};
pub use verify::{BundleVerificationReport, VerificationReport};

pub const KERNEL_VERSION: u32 = 1;
pub const MAX_PARENT_HASHES: usize = 5;
pub const DIGEST_SIZE: usize = 32;
pub const MAX_SCHEMA_ID_LEN: usize = 64;
pub const MAX_SCHEMA_AUTHORITY_LEN: usize = 64;
pub const MAX_DOMAIN_TAG_LEN: usize = 32;
pub const MAX_ISSUER_ID_LEN: usize = 64;
pub const MAX_SUBJECT_ID_LEN: usize = 64;
pub const MAX_CLAIM_LEN: usize = 1024;
pub const MAX_EVIDENCE_LEN: usize = 4096;
pub const MAX_POLICY_LEN: usize = 2048;
pub const MAX_TRACE_EVENT_LEN: usize = 1024;
pub const MAX_BUNDLE_SIZE: usize = 100;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum HashAlgorithm {
    Sha256 = 0x01,
}

impl HashAlgorithm {
    pub const fn from_u8(value: u8) -> Option<Self> {
        match value {
            0x01 => Some(Self::Sha256),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum SignatureAlgorithm {
    Ed25519 = 0x01,
}

impl SignatureAlgorithm {
    pub const fn from_u8(value: u8) -> Option<Self> {
        match value {
            0x01 => Some(Self::Ed25519),
            _ => None,
        }
    }
}

pub mod bounded {
    macro_rules! bounded_string {
        ($name:ident, $max_len:expr) => {
            #[derive(Debug, Clone, Copy, PartialEq, Eq)]
            pub struct $name {
                bytes: [u8; $max_len],
                len: u8,
            }

            impl $name {
                pub const fn new() -> Self {
                    Self {
                        bytes: [0; $max_len],
                        len: 0,
                    }
                }

                #[allow(clippy::should_implement_trait)]
                pub fn from_str(value: &str) -> crate::Result<Self> {
                    Self::from_bytes(value.as_bytes())
                }

                pub fn from_bytes(bytes: &[u8]) -> crate::Result<Self> {
                    if bytes.is_empty() {
                        return Err(crate::Error::EmptyValue);
                    }
                    if bytes.len() > $max_len {
                        return Err(crate::Error::ValueTooLong);
                    }
                    let mut value = Self::new();
                    value.bytes[..bytes.len()].copy_from_slice(bytes);
                    value.len = bytes.len() as u8;
                    Ok(value)
                }

                pub fn as_bytes(&self) -> &[u8] {
                    &self.bytes[..self.len as usize]
                }

                pub fn as_str(&self) -> crate::Result<&str> {
                    core::str::from_utf8(self.as_bytes()).map_err(|_| crate::Error::InvalidUtf8)
                }

                pub fn is_empty(&self) -> bool {
                    self.len == 0
                }
            }

            impl Default for $name {
                fn default() -> Self {
                    Self::new()
                }
            }
        };
    }

    bounded_string!(SchemaId, crate::MAX_SCHEMA_ID_LEN);
    bounded_string!(SchemaAuthority, crate::MAX_SCHEMA_AUTHORITY_LEN);
    bounded_string!(DomainTag, crate::MAX_DOMAIN_TAG_LEN);
    bounded_string!(IssuerId, crate::MAX_ISSUER_ID_LEN);
    bounded_string!(SubjectId, crate::MAX_SUBJECT_ID_LEN);
    bounded_string!(ClaimId, 64);
    bounded_string!(EvidenceId, 64);
    bounded_string!(PolicyId, 64);
    bounded_string!(TraceId, 64);
    bounded_string!(BundleId, 64);
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Digest(pub [u8; DIGEST_SIZE]);

impl Digest {
    pub const fn new(bytes: [u8; DIGEST_SIZE]) -> Self {
        Self(bytes)
    }

    pub const fn zero() -> Self {
        Self([0; DIGEST_SIZE])
    }

    pub fn as_bytes(&self) -> &[u8; DIGEST_SIZE] {
        &self.0
    }
}

impl Default for Digest {
    fn default() -> Self {
        Self::zero()
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ParentHashes {
    hashes: [Digest; MAX_PARENT_HASHES],
    count: u8,
}

impl ParentHashes {
    pub const fn new() -> Self {
        Self {
            hashes: [Digest::zero(); MAX_PARENT_HASHES],
            count: 0,
        }
    }

    pub fn push(&mut self, hash: Digest) -> Result<()> {
        if self.count as usize >= MAX_PARENT_HASHES {
            return Err(Error::TooManyParents);
        }
        self.hashes[self.count as usize] = hash;
        self.count += 1;
        Ok(())
    }

    pub fn as_slice(&self) -> &[Digest] {
        &self.hashes[..self.count as usize]
    }

    pub fn len(&self) -> usize {
        self.count as usize
    }

    pub fn is_empty(&self) -> bool {
        self.count == 0
    }
}

impl Default for ParentHashes {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Ed25519PublicKey(pub [u8; 32]);

impl Ed25519PublicKey {
    pub const fn new(bytes: [u8; 32]) -> Self {
        Self(bytes)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Ed25519Signature(pub [u8; 64]);

impl Ed25519Signature {
    pub const fn new(bytes: [u8; 64]) -> Self {
        Self(bytes)
    }
}
