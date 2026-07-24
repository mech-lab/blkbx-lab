# Receipt Domain Model

BLKBX Lab keeps one shared receipt envelope and layers domain-specific framing above it.

## Shared Artifact Set

The shipped public artifact set is:

- `ink_manifest.v2.json`
- `ink_receipt.v2.json`
- `receipt_comparison.v2.json`

## Shared Evidence Inputs

The primary trace path emits a common evidence shape:

- `action.json`: action proposal and scenario outcome
- `runtime.json`: execution topology and replay posture
- `demo_mapping.json`: deterministic demo scenario mapping
- `model_waist.json`: normalized model identity, invocation, observation, and runtime metadata

Those inputs are summarized and hashed into `ink_manifest.v2.json`.

## Receipt Layer

`ink_receipt.v2.json` carries the signed gate decision over the manifest and policy evaluation path. Verification reports then evaluate:

- structural validity
- trust and signer state
- revocation status when configured
- policy acceptance

## Product Overlays

- `BLKBXS` frames the shared receipt layer as bank-verifiable evidence.
- `MAND8` frames it as insurance and delegated-authority evidence.
- `DUE` frames it as legal defensibility evidence.

The domain overlays change semantics and audiences, not the underlying artifact contract.

BLKBXS UBR is a concrete example of that split. The Universal Banking Receipt body records banking event state and graph links, while the linked `ink.receipt.v2` portable receipt remains the signed trust record.
