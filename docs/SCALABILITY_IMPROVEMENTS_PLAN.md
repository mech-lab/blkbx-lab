# Rust Core Scalability Improvements Plan

## Executive Summary
This document outlines a comprehensive plan to improve the scalability of the inkreceipts-core Rust crate. The plan addresses memory optimization, hashing performance, policy evaluation scaling, data structure improvements, and concurrency enhancements.

## Current Architecture Analysis

### Core Components
1. **Model Waist** (`model_waist.rs`) - Model identity, invocation, observation, runtime, plugin data
2. **Policy Engine** (`policy.rs`) - Policy facts, evaluation, decision making
3. **Receipt System** (`receipt.rs`) - Cryptographic validation, transcript hashing
4. **Digest Operations** (`digest.rs`) - SHA-256 hashing, TLV encoding
5. **Signing/Verification** (`signing.rs`, `verify.rs`) - Ed25519 operations

### Identified Scalability Bottlenecks

| Component | Bottleneck | Impact |
|-----------|------------|--------|
| ModelWaist | Many `Option` fields causing allocations | High memory usage |
| PolicyFacts | Separate boolean fields | Inefficient storage |
| SHA-256 Hashing | Sequential processing | CPU bottleneck |
| Receipt Validation | Multiple hash computations | Latency |
| Data Structures | `Vec<u8>` for small payloads | Allocation overhead |

## Proposed Improvements

### Phase 1: Memory Optimization (Weeks 1-2)

#### 1.1 ModelWaist Refactoring
- Replace `Option<T>` with `MaybeUninit<T>` for zero-cost abstractions
- Use `Cow<'static, str>` for string fields to avoid allocations
- Implement `Default` trait with zero-initialization

#### 1.2 Memory Pooling
- Create `ReceiptPool` for `ReceiptPayload` instances
- Implement `PolicyFactsPool` for policy evaluation objects
- Add `ModelWaistPool` for model data structures

#### 1.3 SmallVec Integration
- Replace `Vec<u8>` with `SmallVec<[u8; 64]>` for small payloads
- Use `SmallVec` for reason codes and small collections
- Benchmark allocation reduction

### Phase 2: Hashing Optimization (Weeks 2-3)

#### 2.1 Parallel Hashing
- Add `rayon` dependency for parallel SHA-256 operations
- Implement `batch_hash` function for multiple inputs
- Create `HashCache` for frequently used hashes

#### 2.2 Hash Caching
- Cache policy hashes in `PolicyBinding`
- Cache model identity hashes in `ModelIdentityClaim`
- Implement LRU cache for transcript hashes

#### 2.3 Streaming Hashing
- Add streaming support for large payloads
- Implement incremental hashing for receipt transcripts
- Reduce memory footprint for large inputs

### Phase 3: Policy Evaluation Scaling (Weeks 3-4)

#### 3.1 Bitflags Refactoring
```rust
// Current: Multiple booleans
struct PolicyFacts {
    requires_human_review: bool,
    binding_effect_present: bool,
    // ...
}

// Proposed: Bitflags
bitflags! {
    struct PolicyFlags: u32 {
        const REQUIRES_HUMAN_REVIEW = 0x1;
        const BINDING_EFFECT_PRESENT = 0x2;
        // ...
    }
}
```

#### 3.2 Lazy Evaluation
- Implement `PolicyEvaluator` with deferred computation
- Add short-circuit evaluation for common cases
- Cache evaluation results for identical inputs

#### 3.3 Parallel Evaluation
- Use thread pool for independent policy checks
- Implement work-stealing for load balancing
- Add configurable concurrency limits

### Phase 4: Data Structure Improvements (Weeks 4-5)

#### 4.1 Custom Serialization
- Implement `serde` with custom binary format
- Add zero-copy deserialization where possible
- Use `bincode` or `postcard` for efficient encoding

#### 4.2 Shared State Management
- Use `Arc<Mutex<T>>` for shared caches
- Implement `DashMap` for concurrent hash maps
- Add read-write locks for high-read scenarios

#### 4.3 Efficient Collections
- Replace `Vec` with `SmallVec` for small collections
- Use `IndexMap` for ordered maps with fast lookup
- Implement custom allocators for hot paths

### Phase 5: Concurrency Enhancements (Weeks 5-6)

#### 5.1 Async I/O Support
- Add `tokio` or `async-std` for async operations
- Implement async file I/O for manifest loading
- Add async network support for remote verification

#### 5.2 Thread Pool Management
- Create dedicated thread pools for:
  - Hashing operations
  - Policy evaluation
  - Signing/verification
- Implement work-stealing queues
- Add metrics for pool utilization

#### 5.3 Lock-Free Data Structures
- Use `crossbeam` for lock-free queues
- Implement `AtomicU64` for counters
- Add `ArcSwap` for configuration hot-reloading

## Implementation Roadmap

### Milestone 1: Memory Optimization (Week 1-2)
- [ ] Refactor ModelWaist with MaybeUninit
- [ ] Implement ReceiptPool and PolicyFactsPool
- [ ] Integrate SmallVec for small payloads
- [ ] Benchmark memory usage reduction

### Milestone 2: Hashing Optimization (Week 2-3)
- [ ] Add rayon dependency
- [ ] Implement parallel hashing
- [ ] Create HashCache with LRU eviction
- [ ] Benchmark hashing throughput

### Milestone 3: Policy Scaling (Week 3-4)
- [ ] Refactor PolicyFacts with bitflags
- [ ] Implement lazy evaluation
- [ ] Add parallel policy evaluation
- [ ] Benchmark evaluation latency

### Milestone 4: Data Structures (Week 4-5)
- [ ] Implement custom binary serialization
- [ ] Add shared state management
- [ ] Optimize collections with SmallVec
- [ ] Benchmark serialization/deserialization

### Milestone 5: Concurrency (Week 5-6)
- [ ] Add async I/O support
- [ ] Implement thread pools
- [ ] Add lock-free data structures
- [ ] Stress test concurrent workloads

### Milestone 6: Validation (Week 6-7)
- [ ] Comprehensive benchmarking
- [ ] Load testing with large datasets
- [ ] Update documentation
- [ ] Performance regression tests

## Success Criteria

| Metric | Target |
|--------|--------|
| Memory usage reduction | 40% |
| Hashing throughput increase | 3x |
| Policy evaluation latency | <5ms (p99) |
| Concurrent throughput | 1000 req/s |
| Allocation reduction | 50% |

## Risk Mitigation

1. **Breaking Changes**: Use feature flags for gradual rollout
2. **Performance Regressions**: Benchmark before/after each change
3. **Compatibility**: Maintain API stability where possible
4. **Testing**: Expand test suite before refactoring

## Dependencies

- `rayon` - Parallel processing
- `smallvec` - Small vector optimization
- `bitflags` - Efficient boolean storage
- `dashmap` - Concurrent hash maps
- `crossbeam` - Lock-free data structures
- `tokio` - Async runtime (optional)
- `bincode`/`postcard` - Binary serialization

## Next Steps

1. Review and approve this plan
2. Prioritize phases based on business needs
3. Assign implementation tasks
4. Set up benchmarking infrastructure
5. Begin Phase 1 implementation