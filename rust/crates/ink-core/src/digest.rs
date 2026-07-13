use sha2::{Digest, Sha256};

use crate::types::Sha256Digest;

pub trait TranscriptSink {
    fn update(&mut self, bytes: &[u8]);
}

pub struct Sha256Sink(Sha256);

impl Sha256Sink {
    pub fn new() -> Self {
        Self(Sha256::new())
    }

    pub fn finalize(self) -> Sha256Digest {
        let bytes = self.0.finalize();
        let mut digest = [0u8; 32];
        digest.copy_from_slice(&bytes);
        Sha256Digest(digest)
    }
}

impl Default for Sha256Sink {
    fn default() -> Self {
        Self::new()
    }
}

impl TranscriptSink for Sha256Sink {
    fn update(&mut self, bytes: &[u8]) {
        self.0.update(bytes);
    }
}

pub fn sha256(bytes: &[u8]) -> Sha256Digest {
    let mut sink = Sha256Sink::new();
    sink.update(bytes);
    sink.finalize()
}

pub fn write_tlv(sink: &mut impl TranscriptSink, field_id: u16, value: &[u8]) {
    sink.update(&field_id.to_be_bytes());
    sink.update(&(value.len() as u32).to_be_bytes());
    sink.update(value);
}

pub fn write_u8_field(sink: &mut impl TranscriptSink, field_id: u16, value: u8) {
    write_tlv(sink, field_id, &[value]);
}

pub fn write_bool_field(sink: &mut impl TranscriptSink, field_id: u16, value: bool) {
    write_u8_field(sink, field_id, if value { 1 } else { 0 });
}

pub fn write_u32_field(sink: &mut impl TranscriptSink, field_id: u16, value: u32) {
    write_tlv(sink, field_id, &value.to_be_bytes());
}

pub fn write_i64_field(sink: &mut impl TranscriptSink, field_id: u16, value: i64) {
    write_tlv(sink, field_id, &value.to_be_bytes());
}
