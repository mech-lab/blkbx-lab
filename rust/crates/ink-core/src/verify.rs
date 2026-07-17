use crate::{receipt::AttestationStatus, Bundle, Digest, ReceiptEnvelope, Result};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct VerificationReport {
    pub valid: bool,
    pub body_hash_valid: bool,
    pub sealed_hash_valid: bool,
    pub schema_valid: bool,
    pub lifecycle_valid: bool,
    pub attestation_binding_valid: bool,
    pub attestation_status: AttestationStatus,
    pub computed_body_hash: Digest,
    pub computed_sealed_hash: Option<Digest>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BundleVerificationReport {
    pub valid: bool,
    pub root_valid: bool,
    pub receipt_count: u8,
    pub computed_root: Digest,
}

pub fn verify_receipt(receipt: &ReceiptEnvelope) -> Result<VerificationReport> {
    let computed_body_hash = crate::canon::compute_receipt_body_hash(receipt)?;
    let body_hash_valid = computed_body_hash == receipt.body_hash;
    let schema_valid = !receipt.schema_id.is_empty()
        && !receipt.schema_authority.is_empty()
        && !receipt.domain_tag.is_empty();
    let lifecycle_valid = !matches!(
        receipt.lifecycle_state,
        crate::lifecycle::LifecycleState::Draft
    );
    let attestation_status = if receipt.attestation.is_some() {
        AttestationStatus::Present
    } else {
        AttestationStatus::Missing
    };
    let attestation_binding_valid = receipt
        .attestation
        .map(|attestation| attestation.validate(receipt).is_ok())
        .unwrap_or(true);
    let computed_sealed_hash = if receipt.attestation.is_some() {
        Some(crate::canon::compute_sealed_receipt_hash(receipt)?)
    } else {
        None
    };
    let sealed_hash_valid = match (receipt.sealed_hash, computed_sealed_hash) {
        (None, None) => true,
        (Some(expected), Some(actual)) => expected == actual,
        _ => false,
    };
    Ok(VerificationReport {
        valid: body_hash_valid
            && sealed_hash_valid
            && schema_valid
            && lifecycle_valid
            && attestation_binding_valid,
        body_hash_valid,
        sealed_hash_valid,
        schema_valid,
        lifecycle_valid,
        attestation_binding_valid,
        attestation_status,
        computed_body_hash,
        computed_sealed_hash,
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
