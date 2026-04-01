#![allow(dead_code)]

#[cfg(feature = "alloc")]
use alloc::vec::Vec;

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Simplex {
    pub vertices: Vec<u32>,
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct SimplicialComplex {
    pub simplices: Vec<Simplex>,
}
