#![allow(dead_code)]

pub trait MapperBackend {
    type Data;
    type Graph;
    type Error;

    fn compute_mapper(&self, data: &Self::Data) -> Result<Self::Graph, Self::Error>;
}
