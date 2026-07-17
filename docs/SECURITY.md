# Security Policy

## Supported Versions

We provide security updates for the following versions of the project:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.0   | :white_check_mark: |
| < 1.0.0 | :x:                |

## Reporting a Vulnerability

Please report security vulnerabilities by emailing security@blkbxlab.com.
We will acknowledge receipt of your report within 48 hours and provide a
detailed response within 7 days.

## Hardening Measures

### Dependency Management
- All dependencies are regularly audited using `cargo audit`.
- We use `cargo deny` to enforce license and security policies.
- Dependencies are updated to the latest secure versions.

### Code Security
- The codebase forbids unsafe code (`#![forbid(unsafe_code)]`).
- We use property-based testing (proptest) for cryptographic functions.
- Fuzz testing is integrated into the CI pipeline for critical entry points.
- Comprehensive unit and integration tests cover error handling and edge cases.

### Cryptographic Security
- We use the `ed25519-dalek` library for cryptographic signatures.
- All cryptographic operations are reviewed for side-channel resistance.
- Keys are managed through signer config, trust registry, and revocation files under the configured host directory.

### Error Handling and Logging
- Errors are defined as an enum with exhaustive variants.
- Error handling is tested to prevent information leakage.
- Logging is designed to avoid sensitive data exposure.

### Continuous Integration
- CI pipeline includes:
  - `cargo build` for compilation
  - `cargo test` for unit and integration tests
  - `cargo clippy` for linting
  - `cargo deny` for license and security checks
  - `cargo fuzz` for fuzz testing
- The pipeline runs on every push and pull request.

### Release Process
- Before each release, we run a full security audit.
- We update the changelog with security fixes.
- We ensure all dependencies are up-to-date and free of known vulnerabilities.

## Contact

For security-related inquiries, please contact security@blkbxlab.com.
