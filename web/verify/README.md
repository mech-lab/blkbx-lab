# INK Browser Verifier

This directory is the browser-facing companion to the native Rust verifier.

Trust boundary:

- trust root: native Rust verifier crates and `ink-cli`
- browser surface: `web/verify`, powered by the shared `ink-wasm` export
- workflow host: Rails can hand off artifact URLs, but it does not perform verification

## Build

From the repo root:

```bash
web/verify/build.sh
```

That script:

- builds `rust/crates/ink-wasm` for `wasm32-unknown-unknown`
- runs `wasm-bindgen`
- emits the browser package into `web/verify/pkg`

## Local Use

The verifier accepts:

- `ink.receipt.v2`
- optional `ink.manifest.v2`
- optional `ink.verify-policy.v1`
- optional `ink.trust-registry.v1`
- optional `ink.revocations.v1`

If you are running the Rails portal, open:

```text
/verify/index.html?artifact_url=/api/v1/mand8/verifier_artifacts?workspace_id=...
```

That Rails handoff only exists when the selected workspace context truly carries a portable `ink.receipt.v2` companion. The page will load the handoff, call the Rust `verify_artifacts` export, and render:

- a compact pass, warning, or fail summary
- the raw `ink.verification-report.v1` JSON

## Lloyd's Labs Demo Path

The fixed Friday, July 17, 2026 seeded MAND8 Lloyd's scenarios do not yet persist a native `ink.receipt.v2` companion for each `mand8.*` product receipt. In `v1` cleanup:

- those seeded MAND8 handoffs are expected to return unavailable with `PORTABLE_RECEIPT_MISSING`
- browser verification still works for real portable INK artifacts pasted into the page
- browser verification still works for Rails handoff URLs when a workspace truly carries a portable `ink.receipt.v2`

Use the browser verifier as a parity check beside the native CLI, not as a replacement for it.
