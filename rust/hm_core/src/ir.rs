#![allow(dead_code)]

use crate::family::TransportFamilyKind;
use crate::sketches::SignedSketch;

#[derive(Clone, Debug)]
pub struct TraceId(pub u64);

#[derive(Clone, Debug)]
pub struct TransportDigest {
    pub local_steps: u16,
    pub bridge_crossings: u16,
    pub retention_score: f32,
}

#[derive(Clone, Debug)]
pub struct ReproducibilityManifest {
    pub backend_name: &'static str,
    pub schedule_hash: u64,
    pub rust_core_version: &'static str,
}

#[derive(Clone, Debug)]
pub struct TraceManifest {
    pub trace_id: TraceId,
    pub family: TransportFamilyKind,
    pub profile_name: &'static str,
    pub transport: TransportDigest,
    pub sketch: SignedSketch,
    pub reproducibility: ReproducibilityManifest,
}
