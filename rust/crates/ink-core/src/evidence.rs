use crate::bounded::{EvidenceId, SchemaId};
use crate::{hash, Digest, Result, MAX_EVIDENCE_LEN};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Evidence {
    pub id: EvidenceId,
    pub schema_id: SchemaId,
    content: [u8; MAX_EVIDENCE_LEN],
    content_len: u16,
}

impl Evidence {
    pub const fn new() -> Self {
        Self {
            id: EvidenceId::new(),
            schema_id: SchemaId::new(),
            content: [0; MAX_EVIDENCE_LEN],
            content_len: 0,
        }
    }

    pub fn from_slice(schema_id: SchemaId, content: &[u8]) -> Result<Self> {
        let mut evidence = Self::new();
        evidence.id = EvidenceId::from_str("evidence")?;
        evidence.schema_id = schema_id;
        evidence.set_content(content)?;
        Ok(evidence)
    }

    pub fn set_content(&mut self, content: &[u8]) -> Result<()> {
        if content.is_empty() {
            return Err(crate::Error::EmptyValue);
        }
        if content.len() > MAX_EVIDENCE_LEN {
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
        let sequence = [self.schema_id.as_bytes(), self.content()];
        hash::hash_many_labeled(b"evidence", &sequence)
    }
}

impl Default for Evidence {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct EvidenceCommitment {
    pub evidence_id: EvidenceId,
    pub evidence_hash: Digest,
    pub schema_hash: Digest,
}
