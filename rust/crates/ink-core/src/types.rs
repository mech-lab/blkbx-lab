use core::str;

use crate::error::Error;
use crate::limits::{MAX_ID_LEN, MAX_POLICY_ID_LEN, MAX_REASON_CODE_LEN};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Sha256Digest(pub [u8; 32]);

impl Sha256Digest {
    pub const ZERO: Self = Self([0u8; 32]);
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Ed25519PublicKey(pub [u8; 32]);

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Ed25519Signature(pub [u8; 64]);

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TimestampUtc {
    pub unix_seconds: i64,
    pub nanos: u32,
}

impl TimestampUtc {
    pub fn new(unix_seconds: i64, nanos: u32) -> Result<Self, Error> {
        let timestamp = Self {
            unix_seconds,
            nanos,
        };
        timestamp.validate()?;
        Ok(timestamp)
    }

    pub fn validate(&self) -> Result<(), Error> {
        if self.nanos >= 1_000_000_000 {
            return Err(Error::InvalidTimestamp);
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct BoundedBytes<'a, const N: usize> {
    bytes: &'a [u8],
}

impl<'a, const N: usize> BoundedBytes<'a, N> {
    pub fn new(bytes: &'a [u8]) -> Result<Self, Error> {
        validate_non_nul(bytes, N)?;
        Ok(Self { bytes })
    }

    pub fn new_identifier(bytes: &'a [u8]) -> Result<Self, Error> {
        validate_non_nul(bytes, N)?;
        if bytes.iter().copied().any(|byte| !is_identifier_byte(byte)) {
            return Err(Error::InvalidByteClass);
        }
        Ok(Self { bytes })
    }

    pub fn new_reason_code(bytes: &'a [u8]) -> Result<Self, Error> {
        validate_non_nul(bytes, N)?;
        if bytes.iter().copied().any(|byte| !is_reason_code_byte(byte)) {
            return Err(Error::InvalidByteClass);
        }
        Ok(Self { bytes })
    }

    pub fn as_bytes(&self) -> &'a [u8] {
        self.bytes
    }

    pub fn as_str(&self) -> Result<&'a str, Error> {
        str::from_utf8(self.bytes).map_err(|_| Error::InvalidUtf8)
    }
}

pub type ActionId<'a> = BoundedBytes<'a, MAX_ID_LEN>;
pub type ReceiptId<'a> = BoundedBytes<'a, MAX_ID_LEN>;
pub type PolicyId<'a> = BoundedBytes<'a, MAX_POLICY_ID_LEN>;
pub type KeyId<'a> = BoundedBytes<'a, MAX_ID_LEN>;
pub type ReasonCode<'a> = BoundedBytes<'a, MAX_REASON_CODE_LEN>;

fn validate_non_nul(bytes: &[u8], max_len: usize) -> Result<(), Error> {
    if bytes.is_empty() {
        return Err(Error::EmptyValue);
    }
    if bytes.len() > max_len {
        return Err(Error::ValueTooLong);
    }
    if bytes.contains(&0) {
        return Err(Error::ContainsNul);
    }
    Ok(())
}

fn is_identifier_byte(byte: u8) -> bool {
    byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.' | b':' | b'/')
}

fn is_reason_code_byte(byte: u8) -> bool {
    byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.' | b':' | b'/')
}
