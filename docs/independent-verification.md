# Independent Verification

INK `1.0.0` ships a native Rust verification path for current public receipt artifacts.

The verifier surface is:

- `ink-cli` for direct file-based checks
- `ink-tui` for the zero-JS interactive terminal verifier
- `ink-receipt-v2` as the shared Rust compatibility layer for `ink.receipt.v2`

The verifier consumes local files only:

- `ink_receipt.v2.json`
- optional `ink_manifest.v2.json`
- optional `controls.supplied.json`
- optional `trust-registry.json`
- optional `revocations.json`
- optional `verify-policy.json`

The verifier does not call any BLKBX-hosted API, does not require an account, and does not require a browser. In-repo Rails and TypeScript scaffolds do not change that trust boundary.

## Current policy surfaces

- `ink.verify-policy.v1` defines verification requirements such as:
  - require canonical TLV v2
  - allow or reject verify-only encodings
  - require a trusted issuer
  - require revocation checks
  - require manifest, evidence, or controls summary matches when those files are supplied
- `ink.verification-report.v1` is the stable JSON output shape returned by the shared verifier

## Strict vs compatibility verification

The customer-facing zero-JS surfaces default to `BANK_STRICT_POLICY`.

That policy:

- requires `INK-CORE-TLV-V2`
- rejects verify-only legacy encodings
- requires a trusted issuer
- does not allow network access

`ink-host` keeps a compatibility policy for the existing Python and local issuance flow so previously issued compatibility receipts can still be checked through the installed host surface.

## Shared implementation boundary

`ink-receipt-v2` owns current public receipt verification semantics:

- JSON parsing for `ink.receipt.v2`
- transcript encoding dispatch
- signature verification
- trust-registry checks
- revocation-list checks
- manifest and controls summary checks
- projection into the neutral Rust kernel

`ink-host`, `ink-cli`, and `ink-tui` all call that shared layer instead of maintaining separate receipt verification logic.
