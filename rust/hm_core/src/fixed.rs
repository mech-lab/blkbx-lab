#![allow(dead_code)]

/// Minimal fixed-point placeholder (Q16.16).
#[derive(Clone, Copy, Debug, PartialEq, PartialOrd)]
pub struct Q32(pub i32);

impl From<f32> for Q32 {
    fn from(v: f32) -> Self {
        Q32((v * 65536.0) as i32)
    }
}

impl From<Q32> for f32 {
    fn from(v: Q32) -> Self {
        v.0 as f32 / 65536.0
    }
}
