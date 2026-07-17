# INK Evidence Bundle 1.0.0

## Overview
The INK evidence bundle is a portable package that contains all the components needed to verify an INK receipt using the zero-JS native verifier. This bundle format is designed for the `1.0.0` release line, where verification is performed locally using native Rust binaries without any network access or JavaScript.

## Bundle Structure
The evidence bundle contains the following files:

- `ink_receipt.v2.json` - The main receipt data in INK v2 format
- `ink_manifest.v2.json` (optional) - Manifest information about the receipt
- `controls.supplied.json` (optional) - Summary of controls applied to the receipt
- `trust-registry.json` - Trust registry containing trusted issuers and their public keys
- `revocations.json` (optional) - List of revoked public keys
- `verify-policy.json` - Verification policy to be applied
- `README.md` - This document

## Verification Process
To verify an evidence bundle:

1. Extract the bundle contents to a local directory
2. Launch the verifier using one of the following methods:
   - Interactive TUI: `ink-tui` (launches a terminal UI)
   - Command line: `ink verify-receipt --receipt ink_receipt.v2.json`
   - Bundle verification: `ink verify-bundle --receipt ink_receipt.v2.json --manifest ink_manifest.v2.json --controls controls.supplied.json`
3. Follow the prompts to select files for verification
4. Review the verification report showing status, code, transcript encoding, and other details

## Verification Report Fields
The verification report includes:
- `status`: VERIFIED or FAILED
- `code`: Numeric status code
- `transcript_encoding`: Encoding method used (e.g., "tlv2")
- `receipt_profile`: Profile identifier
- `issuer`: Issuer name
- `key_id`: Signing key identifier
- `payload_digest_alg`: Digest algorithm used
- `payload_digest_hex`: Digest value in hex
- `signature_valid`: Whether the signature is cryptographically valid
- `trusted_issuer`: Whether the issuer is in the trust registry
- `revocation_checked`: Whether revocation checking was performed
- `revocation_ok`: Whether the key is not revoked
- `policy_accepted`: Whether the verification policy was satisfied
- `verification_engine`: Always "Rust ink-core"
- `network_required`: Always false for the current zero-JS verification flow
- `checks`: Detailed check results

## Command Line Usage
The verifier provides several command-line interfaces:

### Direct Command Mode
```
ink verify-receipt --receipt <path> [--manifest <path>] [--controls <path>] [--trust-registry <path>] [--revocation-list <path>] [--policy <path>]
```

### Bundle Verification
```
ink verify-bundle --receipt <path> [--manifest <path>] [--controls <path>] [--trust-registry <path>] [--revocation-list <path>] [--policy <path>]
```

### Policy Verification
```
ink verify-policy --policy <path>
```

### TUI Mode
```
ink-tui
```
Launches an interactive terminal UI that guides you through the verification process with field-by-field input.

## Requirements
- Native Rust binary with zero JavaScript
- No network access during verification
- Rust 1.94+ for compilation
- x86_64 architecture (additional architectures supported with appropriate builds)
