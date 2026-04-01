#![allow(dead_code)]

#[cfg(feature = "alloc")]
use alloc::vec::Vec;

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Graph {
    pub nodes: Vec<u32>,
    pub edges: Vec<(u32, u32)>,
}
