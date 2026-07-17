# BLKBX Lab

<p align="center">
  <strong>Model-agnostic INK Receipts with a Rust trust waist and Python product surface.</strong>
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

Do not hand-wave the size of this repo. Generate it.

Preferred:

```bash
tokei .
```

Alternative:

```bash
cloc .
```

Add the generated output here before release-facing use:

| Language | Files | Lines | Code | Comments | Blanks | What it means |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Python | TODO | TODO | TODO | TODO | TODO | SDK, CLI, product facades, demo orchestration |
| Rust | TODO | TODO | TODO | TODO | TODO | trust waist, native verification, PyO3 bridge, CLI/TUI/WASM surfaces |
| Ruby | TODO | TODO | TODO | TODO | TODO | Rails portal scaffold, if present in this checkout |
| TypeScript | TODO | TODO | TODO | TODO | TODO | verifier/browser scaffold, if present in this checkout |
| Markdown | TODO | TODO | TODO | TODO | TODO | docs, specs, architecture, release surface |
| JSON / TOML / YAML | TODO | TODO | TODO | TODO | TODO | schemas, policies, package/workspace config |
| Total | TODO | TODO | TODO | TODO | TODO | full repo footprint |

Blunt rule:

> Do not estimate LOC from GitHub language percentages. Run `tokei` or `cloc`.

Suggested helper:

```bash
mkdir -p scripts
cat > scripts/codebase-size.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

echo "== tokei =="
tokei .

echo
echo "== tracked file extension summary =="
git ls-files \
  | awk '
      {
        n=split($0,a,".");
        if (n > 1) ext=a[n]; else ext="[no extension]";
        count[ext]++
      }
      END {
        for (ext in count) print count[ext], ext
      }
    ' \
  | sort -nr
EOF

chmod +x scripts/codebase-size.sh
./scripts/codebase-size.sh
```

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

## Product Slices

### BLKBXS

Banking-facing receipt infrastructure.

Core claim:

> A bank can independently verify a vendor-produced AI receipt.

BLKBXS is for fintech, banktech, and AI vendors selling into regulated financial institutions.

### MAND8

Insurance-facing receipt infrastructure.

Core claim:

> AI risk should be packaged for underwriting, monitoring, renewal, and claims defensibility.

MAND8 is not just "BLKBXS for insurance."

MAND8 is the insurability slice.

### DUE

Legal-facing receipt infrastructure.

Core claim:

> Legal AI work should produce reviewable, portable, tamper-evident evidence artifacts.

DUE is the legal defensibility slice.

---

## Current Adapter Reality

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
- Rails is scaffold/future portal work, not verifier infrastructure
- TypeScript/browser verifier work is scaffold-level unless proven otherwise by the current checkout
- product packages ride in the same `mechlab-sdk` wheel
- compatibility names exist and should not be confused with the primary public surface
- LOC tables must be generated from the repo, not estimated

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
