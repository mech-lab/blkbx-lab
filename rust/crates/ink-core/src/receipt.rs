use crate::bounded::{DomainTag, IssuerId, SchemaAuthority, SchemaId};
use crate::{Digest, Ed25519PublicKey, Ed25519Signature, ParentHashes, Result, SignatureAlgorithm};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct AttestationRef {
    pub algorithm: SignatureAlgorithm,
    pub public_key: Ed25519PublicKey,
    pub signature: Ed25519Signature,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ReceiptEnvelope {
    pub version: u32,
    pub schema_id: SchemaId,
    pub schema_hash: Digest,
    pub schema_authority: SchemaAuthority,
    pub domain_tag: DomainTag,
    pub subject_hash: Digest,
    pub issuer_id: IssuerId,
    pub sequence: u64,
    pub claim_hash: Digest,
    pub evidence_hash: Digest,
    pub policy_hash: Digest,
    pub trace_hash: Digest,
    pub parent_hashes: ParentHashes,
    pub lifecycle_state: crate::lifecycle::LifecycleState,
    pub canonical_hash: Digest,
    pub attestation: Option<AttestationRef>,
}

impl ReceiptEnvelope {
    pub const fn new() -> Self {
        Self {
            version: crate::KERNEL_VERSION,
            schema_id: SchemaId::new(),
            schema_hash: Digest::zero(),
            schema_authority: SchemaAuthority::new(),
            domain_tag: DomainTag::new(),
            subject_hash: Digest::zero(),
            issuer_id: IssuerId::new(),
            sequence: 0,
            claim_hash: Digest::zero(),
            evidence_hash: Digest::zero(),
            policy_hash: Digest::zero(),
            trace_hash: Digest::zero(),
            parent_hashes: ParentHashes::new(),
            lifecycle_state: crate::lifecycle::LifecycleState::Draft,
            canonical_hash: Digest::zero(),
            attestation: None,
        }
    }

    #[allow(clippy::too_many_arguments)]
    pub fn create(
        schema_id: SchemaId,
        schema_hash: Digest,
        schema_authority: SchemaAuthority,
        domain_tag: DomainTag,
        subject_hash: Digest,
        issuer_id: IssuerId,
        sequence: u64,
        claim_hash: Digest,
        evidence_hash: Digest,
        policy_hash: Digest,
        trace_hash: Digest,
        parent_hashes: ParentHashes,
    ) -> Self {
        let mut receipt = Self::new();
        receipt.schema_id = schema_id;
        receipt.schema_hash = schema_hash;
        receipt.schema_authority = schema_authority;
        receipt.domain_tag = domain_tag;
        receipt.subject_hash = subject_hash;
        receipt.issuer_id = issuer_id;
        receipt.sequence = sequence;
        receipt.claim_hash = claim_hash;
        receipt.evidence_hash = evidence_hash;
        receipt.policy_hash = policy_hash;
        receipt.trace_hash = trace_hash;
        receipt.parent_hashes = parent_hashes;
        receipt.lifecycle_state = crate::lifecycle::LifecycleState::Observed;
        receipt
    }

    pub fn seal(mut self) -> Result<Self> {
        self.lifecycle_state = crate::lifecycle::LifecycleState::Sealed;
        self.canonical_hash = crate::canon::compute_receipt_hash(&self)?;
        Ok(self)
    }

    pub fn with_attestation(mut self, attestation: AttestationRef) -> Self {
        self.attestation = Some(attestation);
        self
    }
}

impl Default for ReceiptEnvelope {
    fn default() -> Self {
        Self::new()
    }
}
