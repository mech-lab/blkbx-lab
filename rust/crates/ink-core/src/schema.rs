use crate::bounded::{DomainTag, SchemaAuthority, SchemaId};
use crate::{hash, Digest, Result, MAX_POLICY_LEN};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Schema {
    pub id: SchemaId,
    pub authority: SchemaAuthority,
    pub domain_tag: DomainTag,
    pub version: u32,
    content: [u8; MAX_POLICY_LEN],
    content_len: u16,
}

impl Schema {
    pub const fn new() -> Self {
        Self {
            id: SchemaId::new(),
            authority: SchemaAuthority::new(),
            domain_tag: DomainTag::new(),
            version: crate::KERNEL_VERSION,
            content: [0; MAX_POLICY_LEN],
            content_len: 0,
        }
    }

    pub fn from_slice(
        id: SchemaId,
        authority: SchemaAuthority,
        domain_tag: DomainTag,
        version: u32,
        content: &[u8],
    ) -> Result<Self> {
        let mut schema = Self::new();
        schema.id = id;
        schema.authority = authority;
        schema.domain_tag = domain_tag;
        schema.version = version;
        schema.set_content(content)?;
        Ok(schema)
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
        let version = self.version.to_be_bytes();
        let sequence = [
            self.id.as_bytes(),
            self.authority.as_bytes(),
            self.domain_tag.as_bytes(),
            &version[..],
            self.content(),
        ];
        hash::hash_many_labeled(b"schema", &sequence)
    }
}

impl Default for Schema {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SchemaCommitment {
    pub schema_id: SchemaId,
    pub schema_hash: Digest,
    pub authority: SchemaAuthority,
    pub domain_tag: DomainTag,
}
