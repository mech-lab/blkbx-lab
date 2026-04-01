//! Deferred Mapper surface for later topology phases.

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MapperDeferredReport {
    pub status: &'static str,
    pub reason: &'static str,
}

pub fn deferred_mapper_status() -> MapperDeferredReport {
    MapperDeferredReport {
        status: "deferred",
        reason: "exact persistence is the primary topology deliverable for this phase",
    }
}
