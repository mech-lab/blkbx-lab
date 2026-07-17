use crate::bounded::{ClaimId, SchemaId, SubjectId};
use crate::{hash, Digest, Result, MAX_CLAIM_LEN};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Claim {
    pub id: ClaimId,
    pub schema_id: SchemaId,
    pub subject_id: SubjectId,
    content: [u8; MAX_CLAIM_LEN],
    content_len: u16,
}

impl Claim {
    pub const fn new() -> Self {
        Self {
            id: ClaimId::new(),
            schema_id: SchemaId::new(),
            subject_id: SubjectId::new(),
            content: [0; MAX_CLAIM_LEN],
            content_len: 0,
        }
    }

    pub fn from_slice(schema_id: SchemaId, subject_id: SubjectId, content: &[u8]) -> Result<Self> {
        let mut claim = Self::new();
        claim.id = ClaimId::from_str("claim")?;
        claim.schema_id = schema_id;
        claim.subject_id = subject_id;
        claim.set_content(content)?;
        Ok(claim)
    }

    pub fn set_content(&mut self, content: &[u8]) -> Result<()> {
        if content.is_empty() {
            return Err(crate::Error::EmptyValue);
        }
        if content.len() > MAX_CLAIM_LEN {
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
        let sequence = [
            self.schema_id.as_bytes(),
            self.subject_id.as_bytes(),
            self.content(),
        ];
        hash::hash_many_labeled(b"claim", &sequence)
    }
}

impl Default for Claim {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ClaimCommitment {
    pub schema_id: SchemaId,
    pub claim_hash: Digest,
    pub subject_hash: Digest,
}
