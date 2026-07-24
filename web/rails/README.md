# Rails Portal Scaffold

This directory is an in-repo Rails scaffold for workflow and account surfaces that sit beside the native verifier.

## Release Boundary

- shipped trust root: native Rust verification plus the root `mechlab-sdk` wheel
- primary docs surface: `blkbx-lab` and `blkbx_lab`
- non-shipping scaffold: `web/rails`

The app is intentionally not part of the public offline-verification claim for the current release line.

## Local Expectations

- Ruby `3.2.x`
- Bundler `2.x`
- PostgreSQL for `db:prepare`

## Local Commands

```bash
cd web/rails
bin/setup
bin/rspec
bin/rake
bin/rails zeitwerk:check
```

## Hosted Issuer

Set `INK_ISSUER_SERVICE_URL` when exercising flows that require portable `ink.receipt.v2` issuance.

BLKBXS UBR receipt creation is fail-closed. `POST /api/v1/blkbxs/ubr_receipts` must receive a hosted issuer response with `portable_receipt_json`; otherwise the request returns `422` and no UBR receipt is persisted.

## BLKBXS UBR API

- `POST /api/v1/blkbxs/ubr_receipts` creates a signed UBR event receipt in a BLKBXS workspace.
- `POST /api/v1/blkbxs/ubr_bundles` builds a same-process UBR graph bundle.
- `GET /api/v1/blkbxs/dashboard` returns graph summaries for the current BLKBXS workspace.
- `GET /api/v1/blkbxs/verifier_artifacts` returns verifier handoff artifacts only when every selected UBR event has a linked portable receipt.

The Rails demo catalog reads `python/blkbx_lab/products/blkbxs/fixtures/smb_loan_demo.json`, the committed fixture produced by the Python BLKBXS scenario pipeline. Keep the UBR-native demo verifier report and synthetic proof labels as domain evidence only; independent acceptance depends on the linked `ink.receipt.v2` artifacts.

Targeted checks:

```bash
bundle exec rspec spec/requests/blkbxs_ubr_workflows_spec.rb spec/services/schema_catalog_spec.rb spec/services/product_catalog_spec.rb spec/requests/shared_bundles_verifier_handoff_spec.rb
```

## Lloyd's Labs Demo Smoke

On Friday, July 17, 2026, the deterministic Lloyd's Labs smoke wrapper is:

```bash
scripts/mand8_lloyds_demo_smoke.sh
```

That wrapper:

- seeds the canonical `lloyds_incident_to_renewal` workspace
- creates the renewal bundle and carrier review request
- records the seeded workflow summary in `artifacts/mand8-lloyds-demo-smoke/mand8`
- requires MAND8 verifier handoff availability when `INK_ISSUER_SERVICE_URL` is configured
- keeps local-only seeded handoff unavailable when no hosted issuer is configured
- runs the native Rust verifier with `ink receipt` over the separate public INK vector in `artifacts/mand8-lloyds-demo-smoke/ink-vector`

Use the other fixed scenarios for local regression paths:

- `lloyds_cyber_happy_path`
- `lloyds_human_review_edge_case`
