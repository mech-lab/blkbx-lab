#![no_std]

#[cfg(feature = "alloc")]
extern crate alloc;

pub mod prelude;
pub mod family;
pub mod adapter;
pub mod native;
pub mod migration;
pub mod scalar;
pub mod sparse;
pub mod ids;
pub mod hash;
pub mod fixed;
pub mod schedule;
pub mod hooks;
pub mod transport;
pub mod connection;
pub mod sheaf;
pub mod graph;
pub mod hypergraph;
pub mod simplicial;
pub mod filtrations;
pub mod topology;
pub mod mapper;
pub mod persistence;
pub mod sketches;
pub mod metrics;
pub mod ir;
pub mod codec;
pub mod errors;
