# BLKBXS UBR Bank-Verifiable Receipts

BLKBXS applies the shared Ink Receipt infrastructure to banking-facing evidence. The current UBR path models a banking workflow as a graph of domain receipts whose trust comes from linked portable INK receipts.

## Current UBR Shape

- Domain schema keys: `blkbxs.ubr.receipt.v1`, `blkbxs.ubr.bundle.v1`, and `blkbxs.ubr.verifier_report.v1`.
- Python public surface: `blkbxs.schema`, `blkbxs.ubr`, `blkbxs.graph`, `blkbxs.bundle`, and `blkbxs.scenarios`.
- Canonical scenario: `blkbxs.scenarios.smb_loan_demo()` returns the generated SMB loan fixture in topological order.
- Rails fixture source: `Blkbxs::DemoCatalog` reads `python/blkbx_lab/products/blkbxs/fixtures/smb_loan_demo.json`; Rails does not maintain a hand-authored scenario copy.

The SMB loan fixture preserves eight events: consent, KYB, documents, cashflow analysis, AI recommendation, human review, loan decision, and conditional approval notice.

## Trust Boundary

The UBR JSON is the banking-domain view. In Rails it is stored in `Receipt#body_json` under `schema_key = blkbxs.ubr.receipt.v1`.

The cryptographic record is the linked `ink.receipt.v2` portable receipt in `portable_receipt_json`. `POST /api/v1/blkbxs/ubr_receipts` calls the shared receipt creation path with mandatory portable signing. If `INK_ISSUER_SERVICE_URL` is unset, the issuer fails, or no portable receipt is returned, the request returns `422` and the transaction rolls back.

The supplied UBR-native `verification` fields, synthetic Ed25519 labels, and demo `verifier_report.json` are domain evidence only. They are not the acceptance gate for BLKBXS UBR. A reviewer should verify the linked `ink.receipt.v2` artifacts through the native INK verifier path.

## Graph And Evidence Validation

BLKBXS validates that every UBR receipt matches `blkbxs.ubr.receipt.v1`, parent receipts resolve inside the same `operation.business_process_id`, receipt IDs are unique, and the graph is acyclic.

Evidence posture is reported from `evidence_manifest.json`. The SMB loan fixture currently reports six verifier-available evidence items and two committed-only sensitive document items.

The AI/human boundary rule is explicit: AI may recommend, extract, or analyze; final credit approval above configurable policy thresholds must carry human review evidence. Thresholds stay in policy metadata, not hardcoded code.

## Rails API Surface

- `POST /api/v1/blkbxs/ubr_receipts` creates one signed UBR event receipt.
- `POST /api/v1/blkbxs/ubr_bundles` builds a same-process UBR graph bundle.
- `GET /api/v1/blkbxs/dashboard` returns workspace graph summaries.
- `GET /api/v1/blkbxs/verifier_artifacts` returns verifier handoff artifacts only when every selected UBR event has a linked portable receipt.

Bundle manifests include graph order, decision summary, evidence disclosure summary, AI/human boundary summary, verifier report summary, and verifier handoff metadata.

## Current Limits

- The banking surface still rides in the root `mechlab-sdk` wheel.
- Full RFC 8785 JCS conformance, UBR-native Ed25519 verification, DID/vLEI resolution, issuer anchoring, status-list checks, and HTTP signature binding remain future hardening work.
