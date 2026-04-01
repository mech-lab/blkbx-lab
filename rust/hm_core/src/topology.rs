#![allow(dead_code)]

pub trait PersistenceBackend {
    type Complex;
    type Diagram;
    type Error;

    fn compute_diagram(&self, complex: &Self::Complex) -> Result<Self::Diagram, Self::Error>;
}
