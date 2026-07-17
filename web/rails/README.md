# Rails Portal Scaffold

This directory is an in-repo Rails scaffold for workflow, portal, and account surfaces that sit beside the native verifier.

Release boundary:

- shipped trust root: Rust verifier crates, root `mechlab-sdk` wheel, `blkbx-lab` and `mechlab` CLIs
- non-shipping scaffold: `web/rails`

The app is intentionally not part of the public zero-JS verification claim for `1.0.0`.

## Local expectations

- Ruby `3.2.x`
- Bundler `2.x`
- PostgreSQL for `db:prepare`

## Local commands

```bash
cd web/rails
bin/setup
bin/rspec
bin/rake
bin/rails zeitwerk:check
```

## Smoke validation without PostgreSQL

Use the DB-less smoke path when you only need to prove boot, routing, and
service wiring for the scaffold:

```bash
cd web/rails
bundle exec rspec spec/smoke
bin/rails zeitwerk:check
```
