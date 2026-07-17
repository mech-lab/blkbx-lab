# Rails Future Portal

> Archived on July 17, 2026. Historical future-state note, not active source-of-truth documentation.

Rails is now carried in-repo as a scaffold for the `1.0.0` line.

That is intentional.

The first thing the product still needs to prove is independent verification, not hosted workflow.

## 1.0.0 boundary

`1.0.0` ships:

- `ink-receipt-v2` for current public receipt verification
- `ink-cli` for file-based verification
- `ink-tui` for the zero-JS interactive verifier
- file-based trust registries, revocation lists, verification policies, and verification reports

`1.0.0` does not ship:

- customer accounts
- hosted receipt databases
- bundle portals
- issuer dashboards
- Rails-backed verification APIs as part of the trust root
- browser or JavaScript verifier surfaces as part of the trust root

## What Rails should do in-repo

The Rails app should sit beside the verifier rather than beneath it.

Rails should own workflow and packaging concerns such as:

- issuers
- signing keys
- customer projects
- receipt inventory
- verification run history
- bundle export
- portal links
- review queues

The independent verifier should remain usable without Rails. The in-repo scaffold is for workflow packaging, not verification authority.

## Compatibility rule

Rails should export the same artifacts the zero-JS verifier already understands:

- `ink_receipt.v2.json`
- `ink_manifest.v2.json`
- `trust-registry.json`
- `revocations.json`
- `verify-policy.json`
- `ink.verification-report.v1`

That way the hosted portal can package and persist workflow state without becoming part of the trust root.

## Architecture sentence

HTML or Rails can package and sell the workflow.

The native Rust verifier is what proves the trust claim first.
