use crate::error::Error;
use crate::limits::MAX_CONTROLS;
use crate::types::{Sha256Digest, TimestampUtc};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ControlType {
    HumanReview,
    Approval,
    DualControl,
    PolicyException,
    SupervisorOverride,
    ExternalAudit,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ControlStatus {
    Present,
    Approved,
    Rejected,
    Expired,
    Invalid,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ControlObservation {
    pub control_type: ControlType,
    pub action_hash: Sha256Digest,
    pub status: ControlStatus,
    pub actor_hash: Sha256Digest,
    pub observed_at: TimestampUtc,
    pub evidence_hash: Option<Sha256Digest>,
}

impl ControlObservation {
    pub fn validate(&self) -> Result<(), Error> {
        self.observed_at.validate()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ControlSet<'a> {
    observations: &'a [ControlObservation],
}

impl<'a> ControlSet<'a> {
    pub fn new(observations: &'a [ControlObservation]) -> Result<Self, Error> {
        let set = Self { observations };
        set.validate()?;
        Ok(set)
    }

    pub fn validate(&self) -> Result<(), Error> {
        if self.observations.len() > MAX_CONTROLS {
            return Err(Error::TooManyControls);
        }
        for observation in self.observations {
            observation.validate()?;
        }
        Ok(())
    }

    pub fn as_slice(&self) -> &'a [ControlObservation] {
        self.observations
    }
}
