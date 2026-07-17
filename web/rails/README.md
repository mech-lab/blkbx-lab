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
