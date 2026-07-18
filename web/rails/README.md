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

## Lloyd's Labs Demo Smoke

On Friday, July 17, 2026, the deterministic Lloyd's Labs smoke wrapper is:

```bash
scripts/mand8_lloyds_demo_smoke.sh lloyds_cyber_happy_path
```

That wrapper:

- seeds the MAND8 happy-path workspace
- creates the renewal bundle and carrier review request
- records the seeded workflow summary in `artifacts/mand8-lloyds-demo-smoke/mand8`
- proves the seeded MAND8 verifier handoff is unavailable until a real portable companion exists
- runs the native Rust verifier with `ink receipt` over the separate public INK vector in `artifacts/mand8-lloyds-demo-smoke/ink-vector`

Use the other fixed scenarios for the edge paths:

- `lloyds_human_review_edge_case`
- `lloyds_incident_to_renewal`
