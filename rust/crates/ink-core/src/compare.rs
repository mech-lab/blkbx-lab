use crate::error::Error;
use crate::policy::Decision;
use crate::receipt::{receipt_transcript_hash, ReceiptPayload};
use crate::types::{ActionId, ReceiptId, Sha256Digest};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct VerifiedReceiptSummary<'a> {
    pub receipt_id: ReceiptId<'a>,
    pub action_id: ActionId<'a>,
    pub action_hash: Sha256Digest,
    pub manifest_hash: Sha256Digest,
    pub decision: Decision,
    pub payload_hash: Sha256Digest,
}

impl<'a> VerifiedReceiptSummary<'a> {
    pub fn from_payload(payload: &'a ReceiptPayload<'a>) -> Result<Self, Error> {
        payload.validate()?;
        Ok(Self {
            receipt_id: payload.receipt_id,
            action_id: payload.action_id,
            action_hash: payload.model.invocation.action_hash,
            manifest_hash: payload.manifest_hash,
            decision: payload.decision,
            payload_hash: receipt_transcript_hash(payload)?,
        })
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ComparisonOut {
    pub comparable: bool,
    pub decision_match: bool,
    pub action_match: bool,
    pub manifest_match: bool,
}

pub fn compare_receipts(
    left: VerifiedReceiptSummary<'_>,
    right: VerifiedReceiptSummary<'_>,
    out: &mut ComparisonOut,
) -> Result<(), Error> {
    out.action_match = left.action_hash == right.action_hash;
    out.manifest_match = left.manifest_hash == right.manifest_hash;
    out.comparable = out.action_match;
    out.decision_match = out.comparable && left.decision == right.decision;
    Ok(())
}
