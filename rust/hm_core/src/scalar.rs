#![allow(dead_code)]

/// Basic scalar abstraction to permit f32/f64 (and later fixed-point).
pub trait Scalar: Copy + core::fmt::Debug {}

impl Scalar for f32 {}
impl Scalar for f64 {}
