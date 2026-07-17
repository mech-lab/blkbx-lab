use crate::bounded::{DomainTag, IssuerId, PublicKeyId, SchemaAuthority, SchemaId};
use crate::{Digest, ParentHashes, Result, SignatureBytes, SignatureProfileId, SignedMessageHash};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ValidityWindow {
    pub not_before_sequence: u64,
    pub not_after_sequence: u64,
}

impl ValidityWindow {
    pub const fn new(not_before_sequence: u64, not_after_sequence: u64) -> Self {
        Self {
            not_before_sequence,
            not_after_sequence,
        }
    }

    pub const fn contains(self, sequence: u64) -> bool {
        sequence >= self.not_before_sequence && sequence <= self.not_after_sequence
    }

    pub const fn is_valid(self) -> bool {
        self.not_before_sequence <= self.not_after_sequence
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AttestationStatus {
    Missing,
    Present,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct AttestationEnvelope {
    pub profile_id: SignatureProfileId,
    pub issuer_id: IssuerId,
    pub public_key_id: PublicKeyId,
    pub signature: SignatureBytes,
    pub signed_message_hash: SignedMessageHash,
    pub sequence: u64,
    pub validity_window: Option<ValidityWindow>,
}

impl AttestationEnvelope {
    pub fn validate(&self, receipt: &ReceiptEnvelope) -> Result<()> {
        if self.issuer_id != receipt.issuer_id || self.sequence != receipt.sequence {
            return Err(crate::Error::InvalidAttestationBinding);
        }
        if self
            .validity_window
            .map(|window| !window.is_valid())
            .unwrap_or(false)
        {
            return Err(crate::Error::InvalidValidityWindow);
        }
        Ok(())
    }
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
    pub body_hash: Digest,
    pub sealed_hash: Option<Digest>,
    pub attestation: Option<AttestationEnvelope>,
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
            body_hash: Digest::zero(),
            sealed_hash: None,
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
        self.body_hash = crate::canon::compute_receipt_body_hash(&self)?;
        self.sealed_hash = None;
        Ok(self)
    }

    pub fn with_attestation(mut self, attestation: AttestationEnvelope) -> Result<Self> {
        attestation.validate(&self)?;
        self.body_hash = crate::canon::compute_receipt_body_hash(&self)?;
        self.attestation = Some(attestation);
        self.sealed_hash = Some(crate::canon::compute_sealed_receipt_hash(&self)?);
        Ok(self)
    }
}

impl Default for ReceiptEnvelope {
    fn default() -> Self {
        Self::new()
    }
}
