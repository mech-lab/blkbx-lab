# BLKBX Lab

<p align="center">
  <strong>Open-source Ink Receipt gates for accountable AI agents.</strong>
</p>

<p align="center">
  Black Box Labs builds model-agnostic INK Receipts with a Rust trust waist and Python product surface.
</p>

<p align="center">
  <a href="https://github.com/mech-lab/blkbx-lab">
    <img alt="repo" src="https://img.shields.io/badge/repo-mech--lab%2Fblkbx--lab-black">
  </a>
  <a href="https://github.com/mech-lab/blkbx-lab/blob/main/LICENSE">
    <img alt="license" src="https://img.shields.io/badge/license-MIT-blue">
  </a>
  <img alt="package" src="https://img.shields.io/badge/package-mechlab--sdk-111111">
  <img alt="python" src="https://img.shields.io/badge/python-SDK%20%2B%20CLI-yellow">
  <img alt="rust" src="https://img.shields.io/badge/rust-no__std%20trust%20waist-orange">
  <img alt="status" src="https://img.shields.io/badge/status-alpha-red">
</p>

---

## Blunt Summary

BLKBX Lab is not a chatbot wrapper.

BLKBX Lab is a receipt engine for AI actions.

The point of this repo is simple:

> A regulated customer should be able to verify an AI evidence artifact locally, without trusting the vendor's hosted dashboard.

The current codebase ships:

- a Python SDK and CLI
- a Rust native trust boundary
- a deterministic `qwen35` demo adapter
- local evidence bundle generation
- signed INK receipt issuance
- receipt verification
- tamper demonstration
- comparison reports
- product facades for `BLKBXS`, `MAND8`, and `DUE`

The codebase is intentionally mixed-language:

| Layer | Language | Job |
| --- | --- | --- |
| Product SDK / CLI | Python | developer-facing workflow, artifacts, demos, product facades |
| Trust waist | Rust | canonical receipt semantics, signing, verification, native boundary |
| Portal scaffolds | Ruby / Rails, TypeScript | future commercial and browser surfaces, not the trust root |
| Docs / schemas / policies | Markdown, JSON, TOML, YAML | public contract, verification policy, release discipline |

The dashboard is not the source of truth.

The receipt is.

The verifier is.

---

## Codebase Size

Hard-written tracked-file snapshot as of Saturday, July 18, 2026:

| Language | LOC | Where |
| --- | ---: | --- |
| Rust | 10,411 | `rust/crates/*` - 10 crates |
| Ruby | 4,934 | `web/rails/*` - Rails multi-tenant backend |
| Python | 8,662 | `python/*` + `products/*-sdk` + `tests/*` |
| JSON | 4,284 | schemas, test vectors, bundles, policy files |
| Markdown | 3,477 | docs, per-crate and per-product READMEs |
| TypeScript | 383 | `packages/ink-ts-verify` |
| TOML | 387 | Cargo manifests, `pyproject.toml` |
| YAML | 386 | CI and misc config |
| CSS | 445 | `web/verify` static page |
| JavaScript | 174 | `web/verify/*.js` |
| HTML | 106 | `web/verify/*.html` |
| **Total tracked** | **33,649** | everything `git ls-files` sees |

These numbers are here on purpose. The repo is not small, and the shape matters.

---

## What the Whole System Is Trying to Do

One idea, three go-to-market wrappers around it:

> A product emits a signed, canonical receipt - a small cryptographic claim that says "this specific evidence was produced by this issuer, under this schema, at this point in its lifecycle." Anyone holding the receipt, the evidence it points to, a trust registry, and a policy file can verify it themselves, offline, without asking the issuer's API or dashboard anything.

`ink-core` and `ink-host` are the shared engine that make a receipt real: hash it, sign it, verify it, and check trust and revocation. `blkbx_lab`, `mand8`, and `due` are three different business vocabularies built on that same engine - AI-agent action receipts, insurance underwriting and risk receipts, and legal-matter defensibility receipts.

`web/rails` is a hosted multi-tenant backend meant to serve all three brands from one deployment. `web/verify` and `packages/ink-ts-verify` are the receiving-party verification surfaces or scaffolds: the piece a bank, insurer, or legal team should be able to run without trusting any hosted BLKBX interface.

---

## Install

The published package is:

```bash
pip install --pre mechlab-sdk
```

Optional extras:

```bash
pip install --pre "mechlab-sdk[research]"
pip install --pre "mechlab-sdk[experimental]"
pip install --pre "mechlab-sdk[all]"
```

The primary CLI is `blkbx-lab`.

The compatibility CLI is `mechlab`.

The primary Python import is `import blkbx_lab as bl`.

Product facades are carried by the same wheel: `import blkbxs`, `import mand8`, `import due`.

---

## 60-Second Proof

Run the deterministic demo:

```bash
blkbx-lab demo qwen35 --output-dir artifacts/qwen35
```

Verify the receipt:

```bash
blkbx-lab verify artifacts/qwen35/ink_receipt.v2.json
```

Tamper with the receipt:

```bash
blkbx-lab tamper artifacts/qwen35/ink_receipt.v2.json
```

Verify the tampered receipt:

```bash
blkbx-lab verify artifacts/qwen35/ink_receipt.tampered.v2.json
```

Expected result:

- the original receipt verifies
- the tampered receipt fails
- the artifact stays local
- the verification path does not depend on a BLKBX-hosted API

Python version:

```python
import blkbx_lab as bl

result = bl.demo(output_dir="artifacts/qwen35")
print(result.manifest_path)
print(result.receipt_path)

verification = bl.verify(result.receipt_path)
print(verification.report)
```

---

## Public CLI Surface

The current CLI exposes:

```text
blkbx-lab demo       Run the deterministic qwen35 demo
blkbx-lab doctor     Check native runtime, trust policy, and signer state
blkbx-lab trace      Capture deterministic demo evidence
blkbx-lab analyze    Validate a bundle and evaluate a policy
blkbx-lab gate       Issue a signed v2 receipt
blkbx-lab verify     Verify a receipt
blkbx-lab compare    Compare two verified v2 receipts
blkbx-lab tamper     Mutate a receipt for demo purposes
blkbx-lab explain    Explain a receipt decision
blkbx-lab report     Render a human-readable summary
```

This is a real CLI surface. It is not just README copy.

---

## Public Python Surface

Core public calls:

```text
bl.doctor()
bl.trace(...)
bl.analyze(...)
bl.gate(...)
bl.verify(...)
bl.compare(...)
bl.demo(...)
bl.tamper(...)
bl.explain(...)
bl.report(...)
```

Public result objects:

```text
DoctorResult
ActionEvidenceBundle
GateAnalysisResult
InkReceiptResult
ReceiptComparisonPacket
```

---

## What Gets Produced

The receipt flow produces boring files on purpose.

| File | Purpose |
| --- | --- |
| `prompt.txt` | captured prompt text |
| `action.json` | normalized action object |
| `runtime.json` | runtime declaration |
| `demo_mapping.json` | deterministic demo mapping |
| `model_waist.json` | model/runtime waist evidence |
| `ink_manifest.v2.json` | evidence manifest |
| `ink_receipt.v2.json` | signed receipt |
| `ink_receipt.tampered.v2.json` | intentionally mutated demo receipt |
| `receipt_comparison.v2.json` | left/right receipt comparison packet |

The artifacts are meant to be moved, inspected, archived, and verified outside the vendor's system.

---

## Architecture

```text
                     regulated buyer
                           |
                           v
                local receipt verification
                           |
                           v
+--------------------------------------------------+
|                  Rust trust waist                |
|--------------------------------------------------|
| ink-core        no_std receipt kernel            |
| ink-sign        signing boundary                 |
| ink-verify      verification primitives          |
| ink-vectors     deterministic test vectors       |
| ink-receipt-v2  current v2 receipt verifier      |
| ink-cli         file-based verifier CLI          |
| ink-tui         zero-JS terminal verifier        |
| ink-wasm        portable verifier target         |
| ink-host        std host adapter                 |
| ink-py          PyO3 bridge into Python          |
+--------------------------------------------------+
                           ^
                           |
+--------------------------------------------------+
|               Python public surface              |
|--------------------------------------------------|
| blkbx_lab      SDK, CLI, artifact orchestration  |
| blkbxs         banking-facing facade             |
| mand8          insurance-facing facade           |
| due            legal-facing facade               |
| adapters       deterministic qwen35 adapter      |
| policies       demo and verification policies    |
| schemas        public artifact schemas           |
+--------------------------------------------------+
                           ^
                           |
+--------------------------------------------------+
|               Future commercial surfaces         |
|--------------------------------------------------|
| Rails          portal / workflow scaffold        |
| TypeScript     browser/static verifier scaffold  |
+--------------------------------------------------+
```

---

## Why Rust Exists

Rust is here because the trust boundary has to be small.

The Rust layer owns the hard parts:

- receipt semantics
- canonical digest boundaries
- signing and verification
- kernel-level validation
- native verifier behavior
- WASM-compatible verification path
- zero-JS local verification path
- test vectors
- policy enforcement boundaries

`ink-core` is the important design signal:

```rust
#![no_std]
#![forbid(unsafe_code)]
```

That means the kernel is intentionally constrained.

The goal is not "rewrite the app in Rust."

The goal is:

> keep the receipt verifier small enough to audit and harden.

---

## Why Python Exists

Python is here because developers need a usable surface.

The Python layer owns:

- CLI ergonomics
- SDK ergonomics
- deterministic demo flow
- artifact writing
- product facades
- policy inputs
- controls inputs
- report rendering
- packaging

But the Python layer does not silently replace the native trust path.

If `blkbx_lab._ink_native` is unavailable, trust operations fail instead of falling back to a looser Python implementation.

That is intentional.

---

## Why Rails / Ruby Is Not the Trust Root

Rails is a future portal layer.

Rails can eventually handle:

- issuer accounts
- buyer review rooms
- receipt upload
- evidence bundle presentation
- trust registry management
- workflow status
- BLKBXS / MAND8 / DUE commercial UX

Rails should not become the verifier.

The verifier must remain portable and local.

A portal can make verification easier to understand.

It must not be required for verification.

---

## Rust, Python, Rails, and TS at a Glance

### Rust

`rust/crates/` is the trust waist:

- `ink-core` is the `no_std`, `unsafe`-forbidden kernel
- `ink-host` handles file I/O, trust registries, revocations, and signing dispatch
- `ink-receipt-v2` defines the portable evidence-bundle verifier surface
- `ink-cli` and `ink-tui` are real native verification entrypoints
- `ink-wasm` is the browser-facing verifier target, but it is not the primary trust path
- `ink-py` is the PyO3 bridge into Python

### Python

`python/blkbx_lab` is the public SDK and CLI surface. `python/due` and `python/mand8` are thin shims over the real product logic in `products/due-sdk` and `products/mand8-sdk`.

### Rails

`web/rails` is the hosted multi-tenant backend for future commercial workflow and account surfaces. It is real application code, but it is not the verifier and it does not redefine the trust boundary.

### TypeScript and Browser

`packages/ink-ts-verify` is an early-stage TypeScript verifier primitive. `web/verify` is a Rust-backed browser verifier surface over `ink-wasm`, but it remains outside the trust root and only works on real portable INK artifacts.

---

## Product Slices

### BLKBXS

Banking-facing receipt infrastructure and event evidence.

Core claim:

> A bank can independently verify a vendor-produced AI receipt.

BLKBXS is for fintech, banktech, and AI vendors selling into regulated financial institutions.

The current BLKBXS UBR path models a small-business loan workflow as eight Universal Banking Receipt events:

- consent
- KYB
- documents
- cashflow analysis
- AI recommendation
- human review
- loan decision
- conditional approval notice

In the Python package, `blkbxs.scenarios.smb_loan_demo()` loads the committed fixture generated from the UBR demo bundle and orders the graph topologically. Rails imports that packaged fixture through `Blkbxs::DemoCatalog`; it does not hand-author a second copy of the scenario.

The UBR JSON is the banking-domain view stored in receipt `body_json`. The trust record is the linked portable `ink.receipt.v2` issued by the hosted INK issuer. `POST /api/v1/blkbxs/ubr_receipts` requires `INK_ISSUER_SERVICE_URL`; if the issuer is missing, fails, or returns no portable receipt, the transaction rolls back and no unsigned UBR receipt is persisted.

The active BLKBXS UBR contract is documented in [docs/bank-verifiable-receipts.md](docs/bank-verifiable-receipts.md).

### MAND8

Insurance-facing receipt infrastructure.

Core claim:

> AI risk should be packaged for underwriting, monitoring, renewal, and claims defensibility.

MAND8 is not just "BLKBXS for insurance."

MAND8 is the insurability slice.

The public MAND8 Python surface includes `mand8.authority.record()` alongside exposure, control, override, incident, bundle, and schema helpers.

The Lloyd's Labs demo path is documented in [docs/mand8-lloyds-labs-demo.md](docs/mand8-lloyds-labs-demo.md) and uses fixed Friday, July 17, 2026 scenario data.

The external v1 proof flow is:

- `lloyds_incident_to_renewal`

The local deterministic regression scenarios remain:

- `lloyds_cyber_happy_path`
- `lloyds_human_review_edge_case`

### DUE

Legal-facing receipt infrastructure.

Core claim:

> Legal AI work should produce reviewable, portable, tamper-evident evidence artifacts.

DUE is the legal defensibility slice.

---

## Current Adapter Reality

`qwen35` is the installed deterministic demo. Receipt gates are the standard.

The public adapter registry currently supports:

```text
qwen35
qwen35-claims
qwen3.5
qwen/qwen3.5-2b
```

Those aliases resolve to the same installed deterministic demo adapter:

```text
qwen35
```

Unsupported adapters are rejected.

That is good.

It means the current repo is not pretending to support a full model matrix yet.

---

## Trust Boundary

The trust boundary is:

```text
local files -> Rust verifier -> stable report
```

The verifier consumes local artifacts such as:

```text
ink_receipt.v2.json
ink_manifest.v2.json
controls.supplied.json
trust-registry.json
revocations.json
verify-policy.json
```

The important property:

> Verification should not require a BLKBX-hosted API, a vendor account, or a browser.

---

## Repo Map

```text
blkbx-lab/
  python/
    blkbx_lab/                  primary SDK, CLI, adapters, artifacts, evidence, policies
    blkbxs/                     banking facade
      scenarios.py              UBR demo fixture loader
      ubr.py                    UBR event helper
      graph.py                  UBR graph validation
      bundle.py                 UBR bundle export
    mand8/                      insurance facade
    due/                        legal facade
    mech_lab/                   compatibility namespace

  rust/
    crates/
      ink-core/                 no_std, unsafe-forbidden receipt kernel
      ink-sign/                 signing boundary
      ink-verify/               verification primitives
      ink-vectors/              deterministic vectors
      ink-cli/                  file verifier CLI
      ink-wasm/                 WASM verifier target
      ink-host/                 std host adapter
      ink-py/                   PyO3 bridge
      ink-receipt-v2/           v2 receipt verifier layer
      ink-tui/                  terminal verifier

  docs/                         documentation hub, architecture, security, verification
  schemas/                      public artifact schemas
  policies/                     policy files
  examples/                     deterministic demo examples
  tests/                        Python test suite
  scripts/                      release and development scripts
```

---

## Build System

Python packaging is built through `maturin`.

That matters because the Python package is not pure Python.

The package includes a Rust native extension:

```text
blkbx_lab._ink_native
```

The native extension exposes Rust-backed operations to Python:

```text
create_manifest
analyze
gate
verify
compare
doctor
```

---

## Development

Create an environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install for development:

```bash
pip install -e ".[dev]"
```

Run Python tests:

```bash
pytest
```

Run Rust checks:

```bash
cargo check --workspace
cargo test --workspace
```

Run the no-alloc kernel check, if present in this checkout:

```bash
./scripts/check_no_alloc.sh
```

Run the demo:

```bash
blkbx-lab demo qwen35 --output-dir artifacts/qwen35
```

---

## Security Posture

This repo is early.

But the right hardening direction is visible:

- Rust trust waist
- `no_std` kernel
- unsafe code forbidden in the kernel
- no Python fallback for trust operations
- local verification path
- deterministic vectors
- explicit compatibility boundaries
- separate product facades above the receipt layer
- Rails/TypeScript kept outside the trust root

That is the right shape for regulated buyers.

---

## What This Is Not

This is not:

- a general chatbot app
- a hosted-only compliance dashboard
- a prompt logger
- a fake governance UI
- a full production trust registry
- a full model replay platform
- a complete Rails product
- a full multi-adapter runtime matrix
- a finished commercial product

This is the receipt engine and proof path.

---

## Current Limits

Current limits should stay visible:

- public adapter support is still centered on deterministic `qwen35`
- production signing is not the default public path
- BLKBXS UBR Rails create requests are the exception: they require hosted `ink.receipt.v2` issuance and fail closed when signing is unavailable
- Rails is scaffold/future portal work, not verifier infrastructure
- seeded MAND8 Lloyd's demo workspaces require hosted issuer configuration before they expose portable `ink.receipt.v2` verifier handoffs
- product packages ride in the same `mechlab-sdk` wheel
- compatibility names exist and should not be confused with the primary public surface
- the hard-written LOC snapshot should be refreshed when the repo shape changes materially

---

## Known Gaps

- No cross-language conformance suite yet proves Rust, Python, and TypeScript produce byte-identical results from shared vectors.
- Browser verification is real through `web/verify` and `ink-wasm`, but native verification through `ink`, `ink-cli`, and `ink-tui` remains the trust root.
- Python packaging is still one wheel bundling multiple packages, so `due` and `mand8` remain flat top-level import names.
- The Rails backend has meaningful tests, but it should not be treated as equally trusted with the Rust kernel just because it exists in the same repo.
- No independent external security review of the signing and canonicalization scheme has happened yet.

---

## Documentation

Start here:

- [Docs hub](docs/README.md)
- [CLI and API contract](docs/mvp-cli-api-contract.md)
- [Public object spec](docs/public-object-spec.md)
- [Developer architecture](docs/developer-architecture.md)
- [Product architecture](docs/product-architecture.md)
- [Independent verification](docs/independent-verification.md)
- [Security hardening](docs/security-hardening.md)
- [Reproducibility guide](REPRODUCIBILITY.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

---

## One-Line Pitch

BLKBX Lab makes AI systems produce receipts that regulated customers can verify for themselves.

## Developer Pitch

Use Python to wrap AI actions with evidence artifacts.

Use Rust to verify the receipt boundary.

Keep the files portable.

Keep the verifier local.

Do not ask banks, insurers, or legal teams to trust a screenshot of a dashboard.

## Final Rule

No receipt, no trust.

No local verification, no regulated buyer confidence.

No portable artifact, no serious audit trail.
