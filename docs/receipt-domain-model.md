# Receipt Domain Model

All product slices in this repo use the same conceptual receipt envelope even when they speak different market language.

## Shared Envelope

Every receipt-shaped object carries:

- `schema`
- `receipt_id`
- `action_id`
- `issued_at`
- `domain_context`
- `event_trail`
- `human_review`
- `integrity`

## Shared Integrity Stub

This pass does not add heavy cryptography. The integrity block is a clean stub with:

- `digest`: deterministic SHA-256 of canonical JSON
- `signature_algorithm`: `stub-v1`
- `signature`: `null`
- `core_binding`: `null`

That gives each product a stable adapter boundary for later binding into shared INK Receipts core packages.

## Domain Context Split

The envelope stays the same, but the institutional question changes by slice.

### MAND8

MAND8 receipt context centers on:

- exposure units
- underwriting actions
- delegated authority and binder logic
- risk controls
- policy conditions
- incidents
- overrides

In the UK-first MAND8 story, the Authority Receipt is evidence that an AI-assisted action stayed within the delegated authority frame London market operators already use.

### DUE

DUE receipt context centers on:

- matter context
- legal action
- authority checks
- privilege decisions
- disclosure events
- dispute readiness

## Bundle Objects

Bundles are separate export objects that package one or more receipts for a decision-making audience. They remain JSON-serializable and tamper-evident through the same stub integrity pattern.
