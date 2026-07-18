# MAND8 Signer Conformance Tests

## 1. Demo Gating Tests
These tests verify that the demo signer properly enforces gating mechanisms for development and testing environments.

### 1.1 Demo Signer Health Tests
- **Test**: Verify signer health status in demo mode
- **Expected**: HealthStatus::Healthy with latency_ms = 0
- **Purpose**: Ensure demo signer reports healthy state for CI/CD pipelines

### 1.2 Key Rotation State Tests
- **Test**: Verify rotation state transitions (Stable → InProgress → Stable/Failed)
- **Expected**: Proper state transitions and error handling
- **Purpose**: Ensure demo signer correctly models key rotation lifecycle

### 1.3 Revoked Key Rejection Tests
- **Test**: Attempt to sign with a revoked key
- **Expected**: SignerError::KeyRevoked
- **Purpose**: Prevent use of compromised keys in demo environment

### 1.4 Verify-Only Encoding Rejection Tests
- **Test**: Attempt to use verify-only encoding (TLV_V1_LEGACY or JSON_CANONICAL_V1) for signing
- **Expected**: SignerError::CryptoFailure or Backend error
- **Purpose**: Ensure demo signer rejects legacy encodings that shouldn't be used for new signatures

## 2. Production Signer Health Tests
These tests validate that production signers maintain proper health metrics and operational readiness.

### 2.1 Key Metadata Freshness Tests
- **Test**: Verify key_metadata returns current information
- **Expected**: Created_at timestamp within reasonable bounds, correct algorithm
- **Purpose**: Ensure production signer provides accurate key information

### 2.2 Rotation Status Update Tests
- **Test**: Verify rotation_status reflects actual key state
- **Expected**: Stable during normal operation, InProgress during rotation
- **Purpose**: Enable automated key rotation workflows

### 2.3 Trust Registry Mismatch Detection Tests
- **Test**: Simulate trust registry mismatch during signing
- **Expected**: Appropriate error from remote signer
- **Purpose**: Detect and prevent signing with untrusted keys

### 2.4 Revoked Key Revocation Functionality Tests
- **Test**: Execute revoke_key operation and verify key is marked revoked
- **Expected**: Subsequent sign_digest calls return SignerError::KeyRevoked
- **Purpose**: Ensure compromised keys can be promptly revoked

## 3. Test Scenarios

### 3.1 Demo Mode Key Lifecycle
1. Create LocalSigner with key_id "test-key-001"
2. Verify health is Healthy
3. Verify key_metadata shows Stable rotation state
4. Sign a test digest successfully
5. Simulate key revocation (set revoked = true via reflection or test hook)
6. Verify sign_digest returns KeyRevoked error
7. Verify rotation_status still works
8. Simulate rotation start (set rotation = InProgress)
9. Verify sign_digest returns RotationInProgress error
10. Complete rotation (set rotation = Stable, update key material)
11. Verify signing works again with new key material

### 3.2 Production Signer Simulation
1. Create MockRemoteSigner that implements SignerProvider trait
2. Configure mock to return healthy health report
3. Configure mock to return valid key_metadata
4. Configure mock to return valid signatures for known test vectors
5. Verify end-to-end signing workflow works
6. Simulate backend failure scenarios
7. Verify proper error propagation

### 3.3 Trust Registry Mismatch Scenario
1. Configure signer with key_id "trusted-key"
2. Simulate trust registry showing different key_id for same entity
3. Attempt signing operation
4. Verify appropriate trust error is returned
5. Verify audit trail captures the mismatch

### 3.4 Revoked Key Workflow
1. Verify key is initially not revoked
2. Execute revoke_key with reason "compromised"
3. Verify key_metadata shows revoked = true
4. Attempt signing with revoked key
5. Verify SignerError::KeyRevoked is returned
6. Verify subsequent operations continue to reject the key

### 3.5 Verify-Only Encoding Rejection
1. Configure signer to use TLV_V1_LEGACY encoding (simulated)
2. Attempt signing operation
3. Verify rejection with appropriate error
4. Configure signer to use JSON_CANONICAL_V1 encoding (simulated)
5. Attempt signing operation
6. Verify rejection with appropriate error
7. Verify TLV_V2 encoding works correctly

## 4. Expected Outcomes

### 4.1 Demo Mode Test Results
- All health checks pass with usable status
- Key metadata returns consistent, accurate information
- Signing operations succeed for valid, non-revoked keys
- Revoked keys are properly rejected with clear error messages
- Key rotation states properly block signing during transitions
- Verify-only encodings are rejected for signing operations

### 4.2 Production Signer Test Results
- Health checks accurately reflect backend availability
- Key metadata reflects actual key state and attributes
- Signing operations work with properly configured backends
- Error conditions are properly propagated and documented
- Recovery scenarios work correctly after transient failures

### 4.3 Security Property Verification
- No private key material ever leaves the signer boundary
- All cryptographic operations use constant-time algorithms where possible
- Error messages do not leak sensitive information
- Revocation is immediate and persistent
- Rotation states prevent window of vulnerability during key transitions

## 5. Test Implementation Guidelines

### 5.1 Mock Objects
- Create MockSignerProvider implementations for testing
- Use dependency injection to inject mock signers
- Verify call counts and parameters with mocking frameworks
- Simulate network delays and failures for resilience testing

### 5.2 Test Data
- Use standardized test vectors for signing operations
- Include edge cases: empty digests, maximum size digests
- Use known-good key pairs for validation
- Include test vectors for each supported algorithm

### 5.3 Automation
- Integrate with CI/CD pipeline for continuous verification
- Run tests against both demo and production signer configurations
- Generate coverage reports for signer implementation
- Performance benchmarks for signing operations

### 5.4 Reporting
- Clear pass/fail criteria for each test case
- Detailed error messages for failed tests
- Performance benchmarks where relevant
- Security property validation results