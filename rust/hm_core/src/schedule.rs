#![allow(dead_code)]

#[cfg(feature = "alloc")]
use alloc::vec::Vec;

use crate::family::{BridgeSpec, FamilyDescriptor, KernelConformanceReport, TransportRegimeKind};

pub type BlockOpKind = TransportRegimeKind;

#[derive(Clone, Debug, PartialEq)]
pub struct BlockOp {
    pub kind: TransportRegimeKind,
    pub local_index: u16,
    pub repeats: u16,
    pub label: &'static str,
    pub bridge: Option<BridgeSpec>,
}

#[derive(Clone, Debug, PartialEq)]
pub struct HybridSchedule {
    pub descriptor: FamilyDescriptor,
    pub cadence_label: &'static str,
    pub ops: Vec<BlockOp>,
}

impl HybridSchedule {
    pub fn bridge_mask(&self) -> Vec<bool> {
        self.ops
            .iter()
            .map(|op| matches!(op.kind, TransportRegimeKind::GlobalBridge))
            .collect()
    }

    pub fn bridge_count(&self) -> usize {
        self.bridge_mask().into_iter().filter(|flag| *flag).count()
    }

    pub fn conformance(&self) -> KernelConformanceReport {
        let bridge_count = self.bridge_count();
        let passed = !self.ops.is_empty() && (self.descriptor.bridge.is_none() || bridge_count > 0);
        KernelConformanceReport {
            family: self.descriptor.kind,
            passed,
            schedule_length: self.ops.len(),
            bridge_count,
            notes: if passed {
                &["schedule matches descriptor expectations"]
            } else {
                &["schedule is missing required bridge operations"]
            },
        }
    }
}
