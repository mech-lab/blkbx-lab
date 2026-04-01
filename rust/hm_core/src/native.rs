#![allow(dead_code)]

#[cfg(feature = "alloc")]
use alloc::vec;
#[cfg(feature = "alloc")]
use alloc::vec::Vec;

use crate::family::{
    descriptor_for, FamilyDescriptor, KernelConformanceReport, TransportFamilyKind,
    TransportRegimeKind,
};
use crate::schedule::{BlockOp, HybridSchedule};

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct ScalarTransportState {
    pub value: f32,
    pub step_index: u16,
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct TransportSummary {
    pub local_steps: u16,
    pub bridge_crossings: u16,
    pub retention_score: f32,
}

pub trait NativeTransportKernel<State, Summary> {
    type Error;

    fn family(&self) -> TransportFamilyKind;
    fn descriptor(&self) -> &FamilyDescriptor;
    fn schedule(&self) -> &HybridSchedule;
    fn init_state(&self, seed: f32) -> State;
    fn step_local(&self, state: &mut State) -> Result<(), Self::Error>;
    fn cross_bridge(&self, state: &mut State) -> Result<(), Self::Error>;
    fn summarize(&self, state: &State) -> Summary;
}

#[derive(Clone, Debug)]
pub struct CanonicalTransportKernel {
    pub descriptor: FamilyDescriptor,
    pub schedule: HybridSchedule,
    pub local_gain: f32,
    pub bridge_gain: f32,
}

impl CanonicalTransportKernel {
    pub fn new(
        family: TransportFamilyKind,
        ops: Vec<TransportRegimeKind>,
        cadence_label: &'static str,
        local_gain: f32,
        bridge_gain: f32,
    ) -> Self {
        let descriptor = descriptor_for(family);
        let bridge = descriptor.bridge;
        let schedule = HybridSchedule {
            descriptor: descriptor.clone(),
            cadence_label,
            ops: ops
                .into_iter()
                .enumerate()
                .map(|(idx, kind)| BlockOp {
                    kind,
                    local_index: idx as u16,
                    repeats: 1,
                    label: descriptor.canonical_name,
                    bridge: if matches!(kind, TransportRegimeKind::GlobalBridge) {
                        bridge
                    } else {
                        None
                    },
                })
                .collect(),
        };
        Self {
            descriptor,
            schedule,
            local_gain,
            bridge_gain,
        }
    }
}

impl NativeTransportKernel<ScalarTransportState, TransportSummary> for CanonicalTransportKernel {
    type Error = ();

    fn family(&self) -> TransportFamilyKind {
        self.descriptor.kind
    }

    fn descriptor(&self) -> &FamilyDescriptor {
        &self.descriptor
    }

    fn schedule(&self) -> &HybridSchedule {
        &self.schedule
    }

    fn init_state(&self, seed: f32) -> ScalarTransportState {
        ScalarTransportState {
            value: seed,
            step_index: 0,
        }
    }

    fn step_local(&self, state: &mut ScalarTransportState) -> Result<(), Self::Error> {
        state.value *= self.local_gain;
        state.step_index += 1;
        Ok(())
    }

    fn cross_bridge(&self, state: &mut ScalarTransportState) -> Result<(), Self::Error> {
        state.value *= self.bridge_gain;
        state.step_index += 1;
        Ok(())
    }

    fn summarize(&self, state: &ScalarTransportState) -> TransportSummary {
        let bridge_crossings = self.schedule.bridge_count() as u16;
        TransportSummary {
            local_steps: (self.schedule.ops.len() - self.schedule.bridge_count()) as u16,
            bridge_crossings,
            retention_score: state.value,
        }
    }
}

pub fn gated_deltanet_kernel() -> CanonicalTransportKernel {
    CanonicalTransportKernel::new(
        TransportFamilyKind::GatedDeltaNet,
        vec![
            TransportRegimeKind::RecurrentTransport,
            TransportRegimeKind::RecurrentTransport,
            TransportRegimeKind::RecurrentTransport,
            TransportRegimeKind::GlobalBridge,
        ],
        "3:1",
        0.96,
        1.02,
    )
}

pub fn hgrn2_kernel() -> CanonicalTransportKernel {
    CanonicalTransportKernel::new(
        TransportFamilyKind::HGRN2,
        vec![
            TransportRegimeKind::RecurrentTransport,
            TransportRegimeKind::RecurrentTransport,
            TransportRegimeKind::GlobalBridge,
        ],
        "2:1",
        0.95,
        1.01,
    )
}

pub fn retnet_kernel() -> CanonicalTransportKernel {
    CanonicalTransportKernel::new(
        TransportFamilyKind::RetNet,
        vec![
            TransportRegimeKind::Retention,
            TransportRegimeKind::Retention,
            TransportRegimeKind::Retention,
            TransportRegimeKind::Retention,
            TransportRegimeKind::GlobalBridge,
        ],
        "4:1",
        0.97,
        1.0,
    )
}

pub fn hawk_kernel() -> CanonicalTransportKernel {
    CanonicalTransportKernel::new(
        TransportFamilyKind::Hawk,
        vec![
            TransportRegimeKind::RecurrentTransport,
            TransportRegimeKind::Gate,
            TransportRegimeKind::RecurrentTransport,
            TransportRegimeKind::GlobalBridge,
        ],
        "hawk-gated-4",
        0.94,
        1.01,
    )
}

pub fn transnormer_llm_kernel() -> CanonicalTransportKernel {
    CanonicalTransportKernel::new(
        TransportFamilyKind::TransNormerLLM,
        vec![
            TransportRegimeKind::LocalAttention,
            TransportRegimeKind::LocalAttention,
            TransportRegimeKind::Norm,
            TransportRegimeKind::LocalAttention,
            TransportRegimeKind::GlobalBridge,
        ],
        "transnormer-5",
        0.95,
        0.99,
    )
}

pub fn validate_kernel(kernel: &CanonicalTransportKernel) -> KernelConformanceReport {
    let bridge_count = kernel.schedule.bridge_count();
    let passed = bridge_count > 0 && kernel.schedule.ops.len() >= 3;
    KernelConformanceReport {
        family: kernel.family(),
        passed,
        schedule_length: kernel.schedule.ops.len(),
        bridge_count,
        notes: if passed {
            &["kernel satisfies minimum cadence requirements"]
        } else {
            &["kernel failed cadence requirements"]
        },
    }
}
