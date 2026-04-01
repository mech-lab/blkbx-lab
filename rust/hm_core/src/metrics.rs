#![allow(dead_code)]

use crate::ir::TransportDigest;
use crate::sketches::SignedSketch;

pub fn bridge_dependence(digest: &TransportDigest) -> f32 {
    let total = (digest.local_steps + digest.bridge_crossings).max(1) as f32;
    digest.bridge_crossings as f32 / total
}

pub fn tract_retention(digest: &TransportDigest) -> f32 {
    digest.retention_score
}

pub fn topological_susceptibility(sketch: &SignedSketch) -> f32 {
    let total = (sketch.positive_components + sketch.negative_components).max(1) as f32;
    sketch.cancellation_pairs as f32 / total
}
