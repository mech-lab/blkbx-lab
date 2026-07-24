# MAND8 Procurement Readiness

This phase optimizes the next 8-12 weeks around one regulated workflow: MAND8 delegated-authority cyber underwriting, using `lloyds_incident_to_renewal` as the only external v1 proof flow.

## Contracts

- Keep `ink.receipt.v2` as the portable trust contract.
- Keep `mand8.risk_receipt.v1` as the stable insurance-facing domain contract.
- Require a portable `ink.receipt.v2` companion for every partner-facing MAND8 handoff.
- Treat the MAND8 payload as the business record; its trust claim comes from the linked `ink.receipt.v2`, not from new crypto fields inside `mand8.risk_receipt.v1`.
- Keep `demo_file` local-only and require explicit demo consent.

## Reviewer Packet

A procurement-grade reviewer packet contains:

- `ink_receipt.v2.json`
- `ink_manifest.v2.json`
- `verify-policy.json`
- `trust-registry.json` when trusted-issuer checks are required
- `revocations.json` when revocation checks are required
- reviewer instructions and the shared vector corpus reference, `test-vectors/ink-vectors.json`

The hosted Rails workflow may compose and deliver the packet, but the trust root remains local verification through native Rust, browser/WASM parity, TUI, and TypeScript parity over the same vectors.

## Canonical Workflow

The canonical external workflow is `lloyds_incident_to_renewal`.

It must produce:

- a stable `mand8.risk_receipt.v1` risk receipt
- delegated-authority and incident evidence
- a renewal evidence bundle
- a reviewer-ready handoff with a portable `ink.receipt.v2` companion when hosted issuer configuration is present
- insurer/MGA, bank diligence, and investor overlay indexes generated from the same evidence core

## Hosted Issuance Boundary

Production signing is provider-neutral for this phase. The signer integration contract covers health, key metadata, digest signing, rotation status, and key revocation, with cloud-specific KMS/HSM bindings deferred until partner deployment constraints are known.

Local seeded MAND8 demos without `INK_ISSUER_SERVICE_URL` remain handoff-unavailable with `PORTABLE_RECEIPT_MISSING`. That is intentional: the hosted dashboard does not become the trust root when no portable companion exists.

## Commercial Evidence Base

Maintain one shared core corpus and publish overlays from it:

- insurer/MGA procurement overlay as the primary buyer package
- bank diligence and security overlay as the secondary package
- investor and buyer room overlay indexes from the same evidence corpus

Do not maintain unrelated rooms with divergent copies of the same proof artifacts.
