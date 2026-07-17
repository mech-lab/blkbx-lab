use crate::{Claim, Evidence, Policy, ReceiptEnvelope, Result, TraceEvent};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ReplayReport {
    pub valid: bool,
    pub claim_match: bool,
    pub evidence_match: bool,
    pub policy_match: bool,
    pub trace_match: bool,
}

pub fn replay_receipt(
    receipt: &ReceiptEnvelope,
    claim: &Claim,
    evidence: &Evidence,
    policy: &Policy,
    trace_events: &[TraceEvent],
) -> Result<ReplayReport> {
    let claim_match = claim.compute_hash()? == receipt.claim_hash;
    let evidence_match = evidence.compute_hash()? == receipt.evidence_hash;
    let policy_match = policy.compute_hash()? == receipt.policy_hash;
    let trace_match = crate::event::trace_hash(trace_events)? == receipt.trace_hash;
    Ok(ReplayReport {
        valid: claim_match && evidence_match && policy_match && trace_match,
        claim_match,
        evidence_match,
        policy_match,
        trace_match,
    })
}
