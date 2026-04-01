#![allow(dead_code)]

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct SignedSketch {
    pub positive_components: u32,
    pub negative_components: u32,
    pub cancellation_pairs: u32,
    pub cycle_hint: u32,
}
