use crate::{Bundle, Digest, ReceiptEnvelope, Result};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VerificationReport {
    pub valid: bool,
    pub hash_valid: bool,
    pub schema_valid: bool,
    pub lifecycle_valid: bool,
    pub attestation_present: bool,
    pub computed_hash: Digest,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BundleVerificationReport {
    pub valid: bool,
    pub root_valid: bool,
    pub receipt_count: u8,
    pub computed_root: Digest,
}

pub fn verify_receipt(receipt: &ReceiptEnvelope) -> Result<VerificationReport> {
    let computed_hash = crate::canon::compute_receipt_hash(receipt)?;
    let hash_valid = computed_hash == receipt.canonical_hash;
    let schema_valid = !receipt.schema_id.is_empty()
        && !receipt.schema_authority.is_empty()
        && !receipt.domain_tag.is_empty();
    let lifecycle_valid = !matches!(
        receipt.lifecycle_state,
        crate::lifecycle::LifecycleState::Draft
    );
    Ok(VerificationReport {
        valid: hash_valid && schema_valid && lifecycle_valid,
        hash_valid,
        schema_valid,
        lifecycle_valid,
        attestation_present: receipt.attestation.is_some(),
        computed_hash,
    })
}

pub fn verify_bundle(bundle: &Bundle) -> Result<BundleVerificationReport> {
    let computed_root = bundle.compute_root()?;
    let root_valid = computed_root == bundle.root_hash;
    Ok(BundleVerificationReport {
        valid: root_valid,
        root_valid,
        receipt_count: bundle.receipts().len() as u8,
        computed_root,
    })
}
