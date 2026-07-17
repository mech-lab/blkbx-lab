# Bank-Verifiable Receipts

BLKBXS applies the shared Ink Receipt infrastructure to banking-facing evidence.

## What Gets Verified

A bank-verifiable receipt answers whether a concrete action can be replayed, inspected, and challenged through:

- manifest integrity
- signed receipt integrity
- trust registry checks
- revocation checks when configured
- policy outcome reporting

## Why It Matters for Banks

Banking adoption depends on verifiable operational evidence rather than only model claims. BLKBXS uses the shared receipt layer to give reviewers a local proof path for actions that need control, audit, and challenge handling.

## Current Artifact Shape

The active public artifact set remains:

- `ink_manifest.v2.json`
- `ink_receipt.v2.json`
- `receipt_comparison.v2.json`

## Current Limits

- The current public demo path is still the bundled `qwen35` deterministic demo.
- The banking surface is a thin facade over the root runtime rather than a separate published package line.
