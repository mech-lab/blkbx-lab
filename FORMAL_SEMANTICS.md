# INK Receipts Formal Semantics Draft

This document defines the minimum formal surface for the `INK Receipts` v1 kernel.

## Receipt Validity

A receipt is valid iff all of the following hold:

1. The receipt decodes under the canonical receipt grammar.
2. `schema_id`, `schema_authority`, and `domain_tag` are non-empty.
3. The lifecycle state is a declared kernel lifecycle state.
4. The declared `canonical_hash` equals `H(canonical_bytes(receipt_with_zero_hash))`.
5. If an attestation is present, its algorithm identifier is known to the verifier.

## Canonical Encoding

The kernel canonical encoding is a versioned bounded binary format:

1. Magic prefix `INKR`
2. Big-endian numeric fields
3. Length-prefixed bounded identifier fields
4. Fixed-width 32-byte digest fields
5. Ordered parent hash list
6. Optional attestation block with explicit presence byte

The canonical hash is always computed over the canonical encoding with the `canonical_hash` field zeroed.

## Hash Commitment

`receipt_hash = SHA-256(canonical_bytes(receipt_with_zero_hash))`

The receipt hash therefore commits to:

- schema binding
- subject hash
- issuer identifier
- sequence
- claim hash
- evidence hash
- policy hash
- trace hash
- parent hashes
- lifecycle state
- attestation metadata

## Schema Binding

Schema binding is the tuple:

- `schema_id`
- `schema_hash`
- `schema_authority`
- `domain_tag`

The kernel does not interpret product-specific schema meaning. It only binds the receipt to that schema tuple.

## Parent-Child Relation

A receipt may reference zero or more parent receipt hashes. A parent-child link is valid iff:

1. every parent hash is well-formed
2. the parent list length is within the bounded kernel limit

Host and product layers may impose stronger lineage rules above the kernel.

## Bundle Validity

A bundle is valid iff:

1. its member receipt hash list is within the bounded kernel limit
2. its `root_hash` equals the deterministic root over the ordered member hash list

The current kernel root is an ordered SHA-256 commitment over the member digests.

## Replay Equivalence

Replay succeeds iff the recomputed:

- claim hash
- evidence hash
- policy hash
- trace hash

all equal the committed receipt hashes.

## Diff Relation

The kernel diff relation compares two receipts across these dimensions:

- schema
- claim
- evidence
- policy
- trace
- parent lineage
- lifecycle state

The diff kind is `Unchanged`, a single-axis change, or `Multiple`.

## Lifecycle Transition Table

Allowed transitions:

- `Draft -> Observed`
- `Observed -> Validated`
- `Validated -> Attested`
- `Validated -> Sealed`
- `Attested -> Sealed`
- `Sealed -> Superseded`
- `Sealed -> Revoked`
- `Sealed -> Expired`
- `Expired -> Renewed`
- `Renewed -> Sealed`

Identity transitions are also permitted.
