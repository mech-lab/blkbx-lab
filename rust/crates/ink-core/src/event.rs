use crate::bounded::{IssuerId, TraceId};
use crate::{hash, Digest, Result, MAX_TRACE_EVENT_LEN};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum TraceEventType {
    Observation = 0x01,
    Decision = 0x02,
    Attestation = 0x03,
    Replay = 0x04,
    Compare = 0x05,
}

impl TraceEventType {
    pub const fn from_u8(value: u8) -> Option<Self> {
        match value {
            0x01 => Some(Self::Observation),
            0x02 => Some(Self::Decision),
            0x03 => Some(Self::Attestation),
            0x04 => Some(Self::Replay),
            0x05 => Some(Self::Compare),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TraceEvent {
    pub id: TraceId,
    pub kind: TraceEventType,
    pub subject_hash: Digest,
    pub input_hash: Digest,
    pub output_hash: Digest,
    pub policy_hash: Digest,
    pub previous_event_hash: Digest,
    pub actor: IssuerId,
    pub sequence: u64,
    content: [u8; MAX_TRACE_EVENT_LEN],
    content_len: u16,
}

impl TraceEvent {
    pub const fn new() -> Self {
        Self {
            id: TraceId::new(),
            kind: TraceEventType::Observation,
            subject_hash: Digest::zero(),
            input_hash: Digest::zero(),
            output_hash: Digest::zero(),
            policy_hash: Digest::zero(),
            previous_event_hash: Digest::zero(),
            actor: IssuerId::new(),
            sequence: 0,
            content: [0; MAX_TRACE_EVENT_LEN],
            content_len: 0,
        }
    }

    pub fn from_slice(kind: TraceEventType, actor: IssuerId, content: &[u8]) -> Result<Self> {
        let mut event = Self::new();
        event.id = TraceId::from_str("event")?;
        event.kind = kind;
        event.actor = actor;
        event.set_content(content)?;
        Ok(event)
    }

    pub fn set_content(&mut self, content: &[u8]) -> Result<()> {
        if content.is_empty() {
            return Err(crate::Error::EmptyValue);
        }
        if content.len() > MAX_TRACE_EVENT_LEN {
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
        let kind = [self.kind as u8];
        let seq = self.sequence.to_be_bytes();
        let sequence = [
            &kind[..],
            self.subject_hash.as_bytes(),
            self.input_hash.as_bytes(),
            self.output_hash.as_bytes(),
            self.policy_hash.as_bytes(),
            self.previous_event_hash.as_bytes(),
            self.actor.as_bytes(),
            &seq[..],
            self.content(),
        ];
        hash::hash_many_labeled(b"trace_event", &sequence)
    }
}

impl Default for TraceEvent {
    fn default() -> Self {
        Self::new()
    }
}

pub fn trace_hash(events: &[TraceEvent]) -> Result<Digest> {
    use sha2::{Digest as ShaDigest, Sha256};

    if events.len() > 32 {
        return Err(crate::Error::ValueTooLong);
    }
    let mut hasher = Sha256::new();
    hasher.update(b"INK-V1");
    hasher.update((b"trace_sequence".len() as u16).to_be_bytes());
    hasher.update(b"trace_sequence");
    for event in events {
        let digest = event.compute_hash()?;
        hasher.update((digest.as_bytes().len() as u32).to_be_bytes());
        hasher.update(digest.as_bytes());
    }
    let result = hasher.finalize();
    let mut digest = [0u8; crate::DIGEST_SIZE];
    digest.copy_from_slice(&result);
    Ok(Digest(digest))
}
