use crate::bounded::{PolicyId, SchemaId};
use crate::{hash, Digest, Result, MAX_POLICY_LEN};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum PolicyDecision {
    Pass = 0x01,
    Fail = 0x02,
    Warn = 0x03,
    Review = 0x04,
    Unknown = 0x05,
}

impl PolicyDecision {
    pub const fn from_u8(value: u8) -> Option<Self> {
        match value {
            0x01 => Some(Self::Pass),
            0x02 => Some(Self::Fail),
            0x03 => Some(Self::Warn),
            0x04 => Some(Self::Review),
            0x05 => Some(Self::Unknown),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Policy {
    pub id: PolicyId,
    pub schema_id: SchemaId,
    pub decision: PolicyDecision,
    content: [u8; MAX_POLICY_LEN],
    content_len: u16,
}

impl Policy {
    pub const fn new() -> Self {
        Self {
            id: PolicyId::new(),
            schema_id: SchemaId::new(),
            decision: PolicyDecision::Unknown,
            content: [0; MAX_POLICY_LEN],
            content_len: 0,
        }
    }

    pub fn from_slice(
        schema_id: SchemaId,
        decision: PolicyDecision,
        content: &[u8],
    ) -> Result<Self> {
        let mut policy = Self::new();
        policy.id = PolicyId::from_str("policy")?;
        policy.schema_id = schema_id;
        policy.decision = decision;
        policy.set_content(content)?;
        Ok(policy)
    }

    pub fn set_content(&mut self, content: &[u8]) -> Result<()> {
        if content.is_empty() {
            return Err(crate::Error::EmptyValue);
        }
        if content.len() > MAX_POLICY_LEN {
            return Err(crate::Error::ValueTooLong);
        }
        self.content[..content.len()].copy_from_slice(content);
        self.content_len = content.len() as u16;
        Ok(())
    }

    pub fn content(&self) -> &[u8] {
        &self.content[..self.content_len as usize]
    }

    pub fn compute_hash(&self) -> Result<Digest> {
        let decision = [self.decision as u8];
        let sequence = [self.schema_id.as_bytes(), &decision[..], self.content()];
        hash::hash_many_labeled(b"policy", &sequence)
    }
}

impl Default for Policy {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct PolicyCommitment {
    pub policy_id: PolicyId,
    pub policy_hash: Digest,
    pub schema_hash: Digest,
}
