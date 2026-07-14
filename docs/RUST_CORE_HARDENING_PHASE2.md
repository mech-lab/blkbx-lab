# Rust Core Hardening - Phase 2 Plan

## Overview
This document outlines the continued hardening plan for the Rust core (inkreceipts-core) after the initial security hardening (v0.7.0). The plan is organized by priority and impact.

## Priority 1: Advanced Cryptographic Security (Critical)

### 1.1 Constant-Time Operations
- **Objective**: Prevent timing attacks on cryptographic operations
- **Tasks**:
  - Audit all cryptographic operations for variable-time execution
  - Use `subtle` crate for constant-time comparisons
  - Implement constant-time signature verification
  - Add timing attack tests to CI

### 1.2 Side-Channel Resistance
- **Objective**: Protect against power analysis, cache timing, and other side-channels
- **Tasks**:
  - Review ed25519-dalek usage for side-channel resistance
  - Implement key blinding for signing operations
  - Add memory zeroization for sensitive data
  - Use `zeroize` crate for automatic memory clearing

### 1.3 Secure Random Generation
- **Objective**: Ensure cryptographically secure randomness
- **Tasks**:
  - Replace `rand::random()` with `rand::rngs::OsRng` or `getrandom`
  - Add entropy source validation
  - Implement deterministic randomness for testing only
  - Add randomness quality tests

## Priority 2: Memory Safety & Bounds Checking (High)

### 2.1 Buffer Operations
- **Objective**: Eliminate buffer overflow/underflow risks
- **Tasks**:
  - Audit all array/slice operations for bounds checking
  - Use `get()` instead of direct indexing where possible
  - Add explicit bounds checks with meaningful errors
  - Implement safe wrapper types for fixed-size buffers

### 2.2 Zeroization
- **Objective**: Prevent sensitive data leakage in memory
- **Tasks**:
  - Implement `Zeroize` trait for all key types
  - Add `Drop` implementations that zero memory
  - Use `secrecy` crate for secret types
  - Test memory clearing with tools like `valgrind`

## Priority 3: Comprehensive Fuzz Testing (High)

### 3.1 Fuzz Targets
- **Objective**: Discover edge cases and vulnerabilities through automated testing
- **Tasks**:
  - Add fuzz targets for all public parsing functions
  - Fuzz signature verification with malformed inputs
  - Fuzz receipt payload construction/validation
  - Fuzz policy evaluation with adversarial inputs
  - Integrate with `cargo-fuzz` and OSS-Fuzz

### 3.2 Property-Based Testing Expansion
- **Objective**: Verify invariants across all valid inputs
- **Tasks**:
  - Add proptest strategies for all domain types
  - Test cryptographic round-trip properties
  - Test policy evaluation determinism
  - Test serialization/deserialization round-trips

## Priority 4: Performance Optimization (Medium)

### 4.1 Benchmarking
- **Objective**: Establish performance baselines and prevent regressions
- **Tasks**:
  - Add `criterion` benchmarks for critical paths
  - Benchmark signing/verification operations
  - Benchmark receipt construction/validation
  - Benchmark policy evaluation
  - Add benchmark CI job

### 4.2 Optimization
- **Objective**: Improve performance without sacrificing security
- **Tasks**:
  - Profile hot paths with `perf` or `flamegraph`
  - Optimize allocation patterns
  - Use `smallvec` for small collections
  - Implement object pooling for frequent allocations

## Priority 5: Architecture & Maintainability (Medium)

### 5.1 Module Refactoring
- **Objective**: Improve code organization and testability
- **Tasks**:
  - Split large modules into focused submodules
  - Define clear module boundaries and interfaces
  - Reduce circular dependencies
  - Add module-level documentation

### 5.2 Dependency Injection
- **Objective**: Enable better testing and flexibility
- **Tasks**:
  - Define traits for external dependencies (time, RNG, storage)
  - Implement dependency injection pattern
  - Provide test doubles for all external dependencies
  - Remove global state where possible

### 5.3 Configuration Management
- **Objective**: Support environment-specific behavior safely
- **Tasks**:
  - Define configuration schema with validation
  - Implement environment-based configuration
  - Add configuration hot-reloading (if needed)
  - Document all configuration options

## Priority 6: Observability & Debugging (Medium)

### 6.1 Structured Logging
- **Objective**: Enable effective debugging and monitoring
- **Tasks**:
  - Implement `tracing` integration
  - Add structured log fields for correlation
  - Define log levels and sampling
  - Add security-relevant event logging

### 6.2 Metrics & Monitoring
- **Objective**: Enable operational visibility
- **Tasks**:
  - Add Prometheus metrics for key operations
  - Track signing/verification latency
  - Track error rates by type
  - Add health check endpoints

## Priority 7: Release Automation (Low)

### 7.1 Automated Release Process
- **Objective**: Reduce human error in releases
- **Tasks**:
  - Implement `cargo-release` or similar
  - Automate changelog generation from commits
  - Add release validation checks
  - Implement signed releases

## Implementation Order

1. **Week 1-2**: Constant-time operations, side-channel resistance, secure RNG
2. **Week 3-4**: Memory safety, zeroization, bounds checking
3. **Week 5-6**: Fuzz testing, property-based testing expansion
4. **Week 7-8**: Benchmarking, performance optimization
5. **Week 9-10**: Module refactoring, dependency injection
6. **Week 11-12**: Configuration, structured logging, metrics
7. **Week 13-14**: Release automation, documentation

## Success Criteria

- [ ] All cryptographic operations are constant-time
- [ ] Zero high/critical findings from fuzz testing
- [ ] 90%+ code coverage on critical paths
- [ ] No performance regressions >5% on benchmarks
- [ ] All secrets properly zeroized on drop
- [ ] CI passes with all new checks enabled
- [ ] Documentation covers all public APIs
- [ ] Automated release process validated

## Risk Mitigation

- **Breaking Changes**: Use feature flags for gradual rollout
- **Performance Regressions**: Benchmark before/after each change
- **Compatibility**: Maintain API stability where possible
- **Testing**: Expand test suite before refactoring

## Dependencies

- `subtle` - Constant-time operations
- `zeroize` - Memory zeroization
- `secrecy` - Secret type wrappers
- `criterion` - Benchmarking
- `proptest` - Property-based testing
- `cargo-fuzz` - Fuzz testing
- `tracing` - Structured logging
- `config` - Configuration management