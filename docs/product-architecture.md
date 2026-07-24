# Product Architecture

Black Box Labs builds receipt-native infrastructure for high-assurance AI.

## Shipped OSS Surface

The current shipped OSS runtime is the root `mechlab-sdk` distribution:

- primary docs and CLI surface: `blkbx-lab`
- primary Python surface: `blkbx_lab`
- stable product imports from the same wheel: `blkbxs`, `mand8`, `due`

## Product Roles

- `INK Receipts`: the shared proof primitive and trust waist
- `BLKBXS`: banking-facing evidence, UBR event graphs, and verification framing
- `MAND8`: insurance-facing evidence for pricing, underwriting, monitoring, renewals, and claims defensibility
- `DUE`: legal-facing evidence for authority, privilege, disclosure, and dispute readiness

## Source-Slice Layout

The repository carries sibling product source slices under `products/`:

- `products/mand8-sdk/`
- `products/due-sdk/`

Those directories are in-repo source slices. They are not separate shipped package artifacts for the current release line.

## Positioning Boundaries

- MAND8 is not “banking governance with insurance words.”
- DUE is not “MAND8 for legal.”
- BLKBXS, MAND8, and DUE share infrastructure but keep their market language distinct.

## BLKBXS UBR

The current BLKBXS implementation treats Universal Banking Receipt JSON as the banking-domain view and `ink.receipt.v2` as the trust record. The SMB loan scenario is a generated fixture consumed by both Python and Rails, preserving eight events from consent through conditional approval notice.

Rails UBR receipt creation is fail-closed: hosted issuer configuration must produce a portable INK receipt before a UBR event is persisted.
