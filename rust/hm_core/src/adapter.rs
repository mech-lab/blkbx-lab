#![allow(dead_code)]

use crate::family::{FamilyDescriptor, TransportFamilyKind};
use crate::schedule::HybridSchedule;

pub trait FamilyAdapter<External, Trace> {
    fn family(&self) -> TransportFamilyKind;
    fn descriptor(&self) -> &FamilyDescriptor;
    fn schedule(&self) -> &HybridSchedule;
    fn hook_points(&self) -> &[&'static str];
    fn map_trace(&self, input: &External) -> Trace;
}
