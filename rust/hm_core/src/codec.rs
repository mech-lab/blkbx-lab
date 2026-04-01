#![allow(dead_code)]

pub fn encode_u32_le(v: u32) -> [u8; 4] {
    v.to_le_bytes()
}

pub fn decode_u32_le(bytes: [u8; 4]) -> u32 {
    u32::from_le_bytes(bytes)
}
