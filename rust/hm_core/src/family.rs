#![allow(dead_code)]

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum TransportFamilyKind {
    GatedDeltaNet,
    HGRN2,
    RetNet,
    Hawk,
    TransNormerLLM,
    OLMoHybrid,
    Qwen35,
    KimiLinear,
    Custom,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum PortfolioLane {
    NativeCore,
    UnderstandingFirst,
    Migration,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub enum TransportRegimeKind {
    RecurrentTransport,
    Retention,
    LocalAttention,
    GlobalBridge,
    FeedForward,
    Norm,
    ResidualAdd,
    Gate,
    Migration,
    Other,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct BridgeSpec {
    pub cadence: u16,
    pub label: &'static str,
    pub synchronizes_globally: bool,
    pub strength: f32,
}

#[derive(Clone, Debug, PartialEq)]
pub struct FamilyDescriptor {
    pub kind: TransportFamilyKind,
    pub lane: PortfolioLane,
    pub canonical_name: &'static str,
    pub bridge: Option<BridgeSpec>,
    pub long_context_ready: bool,
    pub notes: &'static [&'static str],
}

#[derive(Clone, Debug, PartialEq)]
pub struct KernelConformanceReport {
    pub family: TransportFamilyKind,
    pub passed: bool,
    pub schedule_length: usize,
    pub bridge_count: usize,
    pub notes: &'static [&'static str],
}

pub fn descriptor_for(kind: TransportFamilyKind) -> FamilyDescriptor {
    match kind {
        TransportFamilyKind::GatedDeltaNet => FamilyDescriptor {
            kind,
            lane: PortfolioLane::NativeCore,
            canonical_name: "Gated DeltaNet",
            bridge: Some(BridgeSpec {
                cadence: 4,
                label: "attention_bridge",
                synchronizes_globally: true,
                strength: 1.0,
            }),
            long_context_ready: true,
            notes: &["canonical native kernel", "first validation target"],
        },
        TransportFamilyKind::HGRN2 => FamilyDescriptor {
            kind,
            lane: PortfolioLane::NativeCore,
            canonical_name: "HGRN2",
            bridge: Some(BridgeSpec {
                cadence: 3,
                label: "state_sync_bridge",
                synchronizes_globally: true,
                strength: 0.95,
            }),
            long_context_ready: true,
            notes: &["native kernel", "recurrent transport separation"],
        },
        TransportFamilyKind::RetNet => FamilyDescriptor {
            kind,
            lane: PortfolioLane::NativeCore,
            canonical_name: "RetNet",
            bridge: Some(BridgeSpec {
                cadence: 5,
                label: "retention_bridge",
                synchronizes_globally: true,
                strength: 0.92,
            }),
            long_context_ready: true,
            notes: &["native kernel", "retention-focused transport"],
        },
        TransportFamilyKind::Hawk => FamilyDescriptor {
            kind,
            lane: PortfolioLane::NativeCore,
            canonical_name: "Hawk",
            bridge: Some(BridgeSpec {
                cadence: 4,
                label: "hawk_bridge",
                synchronizes_globally: true,
                strength: 0.9,
            }),
            long_context_ready: true,
            notes: &["native kernel", "gated recurrent transport"],
        },
        TransportFamilyKind::TransNormerLLM => FamilyDescriptor {
            kind,
            lane: PortfolioLane::NativeCore,
            canonical_name: "TransNormerLLM",
            bridge: Some(BridgeSpec {
                cadence: 5,
                label: "norm_bridge",
                synchronizes_globally: true,
                strength: 0.88,
            }),
            long_context_ready: true,
            notes: &["native kernel", "local attention transport"],
        },
        TransportFamilyKind::OLMoHybrid => FamilyDescriptor {
            kind,
            lane: PortfolioLane::UnderstandingFirst,
            canonical_name: "OLMo Hybrid",
            bridge: Some(BridgeSpec {
                cadence: 5,
                label: "olmo_bridge",
                synchronizes_globally: true,
                strength: 1.0,
            }),
            long_context_ready: true,
            notes: &["reference profile", "adapter validation"],
        },
        TransportFamilyKind::Qwen35 => FamilyDescriptor {
            kind,
            lane: PortfolioLane::UnderstandingFirst,
            canonical_name: "Qwen3.5",
            bridge: Some(BridgeSpec {
                cadence: 4,
                label: "gated_attention_bridge",
                synchronizes_globally: true,
                strength: 1.0,
            }),
            long_context_ready: true,
            notes: &["reference proving ground", "first replay target"],
        },
        TransportFamilyKind::KimiLinear => FamilyDescriptor {
            kind,
            lane: PortfolioLane::UnderstandingFirst,
            canonical_name: "Kimi Linear",
            bridge: Some(BridgeSpec {
                cadence: 3,
                label: "kimi_bridge",
                synchronizes_globally: true,
                strength: 0.9,
            }),
            long_context_ready: true,
            notes: &["reference profile", "linear-memory validation"],
        },
        TransportFamilyKind::Custom => FamilyDescriptor {
            kind,
            lane: PortfolioLane::UnderstandingFirst,
            canonical_name: "Custom",
            bridge: None,
            long_context_ready: false,
            notes: &["user supplied schedule"],
        },
    }
}
