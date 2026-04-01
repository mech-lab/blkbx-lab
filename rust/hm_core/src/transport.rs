#![allow(dead_code)]

pub trait Transport<State> {
    type Error;
    fn step(&self, from: &State) -> Result<State, Self::Error>;
}
