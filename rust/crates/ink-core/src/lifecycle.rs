#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum LifecycleState {
    Draft = 0x01,
    Observed = 0x02,
    Validated = 0x03,
    Attested = 0x04,
    Sealed = 0x05,
    Superseded = 0x06,
    Revoked = 0x07,
    Expired = 0x08,
    Renewed = 0x09,
}

impl LifecycleState {
    pub const fn from_u8(value: u8) -> Option<Self> {
        match value {
            0x01 => Some(Self::Draft),
            0x02 => Some(Self::Observed),
            0x03 => Some(Self::Validated),
            0x04 => Some(Self::Attested),
            0x05 => Some(Self::Sealed),
            0x06 => Some(Self::Superseded),
            0x07 => Some(Self::Revoked),
            0x08 => Some(Self::Expired),
            0x09 => Some(Self::Renewed),
            _ => None,
        }
    }
}

pub fn is_valid_transition(from: LifecycleState, to: LifecycleState) -> bool {
    match (from, to) {
        (LifecycleState::Draft, LifecycleState::Observed)
        | (LifecycleState::Observed, LifecycleState::Validated)
        | (LifecycleState::Validated, LifecycleState::Attested)
        | (LifecycleState::Validated, LifecycleState::Sealed)
        | (LifecycleState::Attested, LifecycleState::Sealed)
        | (LifecycleState::Sealed, LifecycleState::Superseded)
        | (LifecycleState::Sealed, LifecycleState::Revoked)
        | (LifecycleState::Sealed, LifecycleState::Expired)
        | (LifecycleState::Expired, LifecycleState::Renewed)
        | (LifecycleState::Renewed, LifecycleState::Sealed) => true,
        _ if from == to => true,
        _ => false,
    }
}
