#![allow(dead_code)]

pub trait PartialSection {
    type Id: Copy;
    type Value;
    fn id(&self) -> Self::Id;
    fn value(&self) -> &Self::Value;
}

pub trait RestrictionMap<S: PartialSection> {
    type Error;
    fn restrict(&self, src: &S) -> Result<S, Self::Error>;
}

pub trait PartialSheaf<S: PartialSection, R: RestrictionMap<S>> {
    fn local_sections(&self) -> &[S];
    fn restrictions(&self) -> &[R];
}
