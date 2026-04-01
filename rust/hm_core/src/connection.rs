#![allow(dead_code)]

pub trait DiscreteConnection<State> {
    type Path;
    type Error;

    fn transport_along(&self, state: &State, path: &Self::Path) -> Result<State, Self::Error>;
}
