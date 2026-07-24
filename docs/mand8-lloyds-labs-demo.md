# MAND8 Lloyd's Labs Demo

This runbook is fixed to Friday, July 17, 2026 demo data.

## Canonical External Scenario

The external v1 proof flow is:

- `lloyds_incident_to_renewal`

This is the procurement-readiness path for a UK insurer/MGA or Lloyd's-adjacent reviewer. It must end with reviewer-ready renewal evidence and, when hosted issuance is configured, a portable `ink.receipt.v2` verifier handoff.

## Local Regression Scenarios

These scenarios remain deterministic for local demos and regression coverage:

- `lloyds_cyber_happy_path`
- `lloyds_human_review_edge_case`

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

Run the canonical external path:

```bash
scripts/mand8_lloyds_demo_smoke.sh
```

Run local regression paths explicitly:

```bash
scripts/mand8_lloyds_demo_smoke.sh lloyds_cyber_happy_path
scripts/mand8_lloyds_demo_smoke.sh lloyds_human_review_edge_case
```

The wrapper:

- seeds or reuses a MAND8 workspace
- creates the Lloyd's case, authority receipt, incidents, bundle, and review request
- records the seeded workspace summary in `artifacts/mand8-lloyds-demo-smoke/mand8`
- materializes a real public INK vector in `artifacts/mand8-lloyds-demo-smoke/ink-vector`
- runs the native Rust verifier with `ink receipt` over that portable INK vector

## Expected MAND8 Handoff State

The verifier handoff state depends on hosted issuer configuration:

- With `INK_ISSUER_SERVICE_URL` configured, the seeded primary MAND8 risk receipt is issued with a mandatory portable `ink.receipt.v2` companion and an issuer-produced `ink.manifest.v2`; workspace, case, and bundle handoff must be available.
- Without hosted issuer configuration, local seeded workspaces remain handoff-unavailable and report `reason_code: "PORTABLE_RECEIPT_MISSING"`.

Check `artifacts/mand8-lloyds-demo-smoke/mand8/summary.json` for `expected_verifier_handoff_available`, `workspace_verifier_handoff`, `case_verifier_handoff`, and `bundle_verifier_handoff`.

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

When hosted issuer configuration is enabled, open the `verify_path` recorded in the MAND8 summary to load the real reviewer packet directly.

## Trust Boundary

The MAND8 portal is a workflow host. The native Rust verifier remains the trust root.
