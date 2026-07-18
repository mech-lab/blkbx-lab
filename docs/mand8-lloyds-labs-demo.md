# MAND8 Lloyd's Labs Demo

This runbook is fixed to Friday, July 17, 2026 demo data.

## Canonical Scenarios

- `lloyds_cyber_happy_path`
- `lloyds_human_review_edge_case`
- `lloyds_incident_to_renewal`

These scenarios stay deterministic so screenshots, receipt IDs, bundle titles, and underwriter copy remain repeatable for the Lloyd's Labs demo.

## Python Surface

The current public MAND8 receipt contract includes:

- `mand8.exposure.emit()`
- `mand8.authority.record()`
- `mand8.control.record()`
- `mand8.override.record()`
- `mand8.incident.record()`
- `mand8.bundle.export()`
- `mand8.schema.validate()`

## Smoke Path

Prerequisites:

- Ruby `3.2.x`
- Bundler `2.x`
- PostgreSQL for the Rails app
- Rust toolchain plus `ink-cli`

Run the happy path:

```bash
scripts/mand8_lloyds_demo_smoke.sh lloyds_cyber_happy_path
```

Run the two edge paths:

```bash
scripts/mand8_lloyds_demo_smoke.sh lloyds_human_review_edge_case
scripts/mand8_lloyds_demo_smoke.sh lloyds_incident_to_renewal
```

The wrapper:

- seeds or reuses a MAND8 workspace
- creates the Lloyd's case, authority receipt, incidents, bundle, and review request
- records the seeded workspace summary in `artifacts/mand8-lloyds-demo-smoke/mand8`
- materializes a real public INK vector in `artifacts/mand8-lloyds-demo-smoke/ink-vector`
- runs the native Rust verifier with `ink receipt` over that portable INK vector

## Expected MAND8 Handoff State

On the fixed Friday, July 17, 2026 seeded MAND8 scenarios, browser verifier handoff is expected to be unavailable.

Check `artifacts/mand8-lloyds-demo-smoke/mand8/summary.json` and confirm:

- `workspace_verifier_handoff.available` is `false`
- `case_verifier_handoff.available` is `false`
- `bundle_verifier_handoff.available` is `false`
- each unavailable handoff reports `reason_code: "PORTABLE_RECEIPT_MISSING"`

This is the truthful `v1` behavior. The seeded Lloyd's demo workspaces do not yet persist a native `ink.receipt.v2` companion for each `mand8.*` product receipt.

## Browser Parity Check

Open `/verify/index.html` and paste the files from `artifacts/mand8-lloyds-demo-smoke/ink-vector`:

- `ink_receipt.v2.json`
- `ink_manifest.v2.json`
- `trust-registry.json`
- `verify-policy.json`

The browser page:

- calls the Rust `verify_artifacts` WASM export
- renders a pass, warning, or fail summary from the Rust report
- shows the raw `ink.verification-report.v1` JSON beside any optional handoff context

## Trust Boundary

The MAND8 portal is a workflow host. The native Rust verifier remains the trust root.
