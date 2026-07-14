//! Memory pooling for frequently allocated structures to reduce allocation overhead.
//!
//! This module provides simple object pools for `PolicyFacts` and `ReceiptPayload`
//! instances, which are allocated frequently during policy evaluation and receipt
//! processing. Pooling reduces heap allocations and improves cache locality.

use crate::policy::PolicyFacts;
use crate::receipt::ReceiptPayload;
use crate::error::Error;

/// A simple fixed-capacity pool for `PolicyFacts` instances.
///
/// The pool stores pre-allocated `PolicyFacts` values in a stack and reuses them
/// across evaluations to avoid repeated heap allocation.
pub struct PolicyFactsPool<const N: usize> {
    items: [Option<PolicyFacts>; N],
    len: usize,
}

impl<const N: usize> PolicyFactsPool<N> {
    /// Create a new pool with `N` pre-allocated slots (all initially empty).
    pub fn new() -> Self {
        Self {
            items: [None; N],
            len: 0,
        }
    }

    /// Acquire a `PolicyFacts` from the pool, or return `None` if the pool is empty.
    ///
    /// The returned value should be returned via [`PolicyFactsPool::release`] when no
    /// longer needed.
    pub fn acquire(&mut self) -> Option<PolicyFacts> {
        if self.len == 0 {
            return None;
        }
        self.len -= 1;
        self.items[self.len].take()
    }

    /// Release a `PolicyFacts` back into the pool.
    ///
    /// If the pool is full, the value is dropped (and thus deallocated).
    pub fn release(&mut self, item: PolicyFacts) {
        if self.len < N {
            self.items[self.len] = Some(item);
            self.len += 1;
        }
        // If full, `item` is dropped here, freeing the allocation.
    }
}

impl<const N: usize> Default for PolicyFactsPool<N> {
    fn default() -> Self {
        Self::new()
    }
}

/// A simple fixed-capacity pool for `ReceiptPayload` instances.
///
/// Similar to [`PolicyFactsPool`] but for receipt payloads, which are larger and
/// thus benefit more from reuse.
pub struct ReceiptPayloadPool<'a, const N: usize> {
    items: [Option<ReceiptPayload<'a>>; N],
    len: usize,
}

impl<'a, const N: usize> ReceiptPayloadPool<'a, N> {
    /// Create a new pool with `N` pre-allocated slots (all initially empty).
    pub fn new() -> Self {
        Self {
            items: [None; N],
            len: 0,
        }
    }

    /// Acquire a `ReceiptPayload` from the pool, or return `None` if empty.
    pub fn acquire(&mut self) -> Option<ReceiptPayload<'a>> {
        if self.len == 0 {
            return None;
        }
        self.len -= 1;
        self.items[self.len].take()
    }

    /// Release a `ReceiptPayload` back into the pool.
    pub fn release(&mut self, item: ReceiptPayload<'a>) {
        if self.len < N {
            self.items[self.len] = Some(item);
            self.len += 1;
        }
    }
}

impl<'a, const N: usize> Default for ReceiptPayloadPool<'a, N> {
    fn default() -> Self {
        Self::new()
    }
}

/// Helper to create a zeroed `PolicyFacts` for pooling.
///
/// This is used to pre-populate pools with reusable instances.
pub fn zeroed_policy_facts() -> PolicyFacts {
    // SAFETY: PolicyFacts is a Copy type with only primitive fields; zeroed is valid.
    // We rely on the fact that all fields are Copy and have a valid zero representation.
    // For enums, we must use a safe default instead of zeroed memory.
    PolicyFacts {
        risk_class: crate::policy::RiskClass::Low,
        requires_human_review: false,
        binding_effect_present: false,
        provider_fallbacks_allowed: false,
        plugin_trust_level: crate::policy::PluginTrustFact::Untrusted,
        runtime_kind: crate::model_waist::RuntimeKind::LocalOpenWeightModel,
        replay_strength: crate::model_waist::ReplayStrength::DeclaredOnly,
        model_class: crate::model_waist::ModelClass::OpenWeight,
    }
}

/// Pre-populate a `PolicyFactsPool` with `count` reusable instances.
pub fn prefill_policy_pool<const N: usize>(pool: &mut PolicyFactsPool<N>, count: usize) -> Result<(), Error> {
    for _ in 0..count {
        if pool.len < N {
            pool.release(zeroed_policy_facts());
        } else {
            break;
        }
    }
    Ok(())
}
