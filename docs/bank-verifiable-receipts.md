# Bank-Verifiable Receipts

The `1.0.0` trust claim is:

> A regulated customer can verify a vendor-produced INK receipt locally, with zero JavaScript and zero verification-time network access.

That claim is substantiated by a native Rust verifier, not a portal.

## What gets verified

For current public artifacts, the verifier checks:

- receipt transcript digest for the declared encoding
- receipt signature
- trusted issuer membership from a supplied trust registry or pinned key
- optional revocation state from a supplied revocation list
- optional manifest hash and evidence summary
- optional controls summary
- projection into the neutral Rust kernel for canonical receipt validation

## Why this matters for banks

The important property is not that BLKBX can display a receipt in a dashboard.

The important property is that a bank can:

1. receive the receipt bundle from a vendor
2. run the verifier locally
3. inspect a stable report
4. make its own trust decision without depending on vendor infrastructure

That is the difference between:

- vendor-hosted evidence presentation
- customer-verifiable evidence artifacts

## Bundle shape

The portable `1.0.0` bundle is:

```text
ink-evidence-bundle/
  ink_receipt.v2.json
  ink_manifest.v2.json          optional
  controls.supplied.json        optional
  trust-registry.json
  revocations.json              optional
  verify-policy.json
  README.md
```

The verifier binary is installed separately. It is not embedded in the bundle.

## Policy posture

The customer-facing strict policy is `BANK_STRICT_POLICY`.

It rejects verify-only compatibility encodings even when those receipts are still cryptographically valid. That preserves a clear distinction between:

- receipts that remain readable for compatibility
- receipts that are acceptable for strict bank verification
