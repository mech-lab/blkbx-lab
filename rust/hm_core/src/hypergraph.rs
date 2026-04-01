#![allow(dead_code)]

#[cfg(feature = "alloc")]
use alloc::vec::Vec;

#[derive(Clone, Debug, Default)]
pub struct HyperEdge {
    pub nodes: Vec<u32>,
}

#[derive(Clone, Debug, Default)]
pub struct HyperGraph {
    pub nodes: Vec<u32>,
    pub hyperedges: Vec<HyperEdge>,
}
