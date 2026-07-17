use crate::{Bundle, BundleDiff, ReceiptEnvelope, Result};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DiffKind {
    Unchanged,
    SchemaChanged,
    ClaimChanged,
    EvidenceChanged,
    PolicyChanged,
    TraceChanged,
    ParentChanged,
    LifecycleChanged,
    Multiple,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ReceiptDiff {
    pub comparable: bool,
    pub same_hash: bool,
    pub schema_changed: bool,
    pub claim_changed: bool,
    pub evidence_changed: bool,
    pub policy_changed: bool,
    pub trace_changed: bool,
    pub parent_changed: bool,
    pub lifecycle_changed: bool,
    pub kind: DiffKind,
}

pub type CompareReport = ReceiptDiff;

pub fn compare_receipts(left: &ReceiptEnvelope, right: &ReceiptEnvelope) -> Result<ReceiptDiff> {
    let schema_changed = left.schema_hash != right.schema_hash
        || left.schema_id != right.schema_id
        || left.schema_authority != right.schema_authority;
    let claim_changed = left.claim_hash != right.claim_hash;
    let evidence_changed = left.evidence_hash != right.evidence_hash;
    let policy_changed = left.policy_hash != right.policy_hash;
    let trace_changed = left.trace_hash != right.trace_hash;
    let parent_changed = left.parent_hashes != right.parent_hashes;
    let lifecycle_changed = left.lifecycle_state != right.lifecycle_state;
    let changed_count = [
        schema_changed,
        claim_changed,
        evidence_changed,
        policy_changed,
        trace_changed,
        parent_changed,
        lifecycle_changed,
    ]
    .iter()
    .filter(|changed| **changed)
    .count();
    let kind = match changed_count {
        0 => DiffKind::Unchanged,
        1 if schema_changed => DiffKind::SchemaChanged,
        1 if claim_changed => DiffKind::ClaimChanged,
        1 if evidence_changed => DiffKind::EvidenceChanged,
        1 if policy_changed => DiffKind::PolicyChanged,
        1 if trace_changed => DiffKind::TraceChanged,
        1 if parent_changed => DiffKind::ParentChanged,
        1 if lifecycle_changed => DiffKind::LifecycleChanged,
        _ => DiffKind::Multiple,
    };
    Ok(ReceiptDiff {
        comparable: left.subject_hash == right.subject_hash,
        same_hash: left.canonical_hash == right.canonical_hash,
        schema_changed,
        claim_changed,
        evidence_changed,
        policy_changed,
        trace_changed,
        parent_changed,
        lifecycle_changed,
        kind,
    })
}

pub fn compare_bundles(left: &Bundle, right: &Bundle) -> Result<BundleDiff> {
    let mut added = 0u8;
    for hash in right.receipts() {
        if !left.receipts().contains(hash) {
            added = added.saturating_add(1);
        }
    }
    let mut removed = 0u8;
    for hash in left.receipts() {
        if !right.receipts().contains(hash) {
            removed = removed.saturating_add(1);
        }
    }
    Ok(BundleDiff {
        added_count: added,
        removed_count: removed,
        reordered: left.receipts() != right.receipts()
            && left.receipts().len() == right.receipts().len()
            && added == 0
            && removed == 0,
    })
}
