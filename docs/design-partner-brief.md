# MAND8 Design Partner Brief

## 1. Runbook
- Key bootstrap procedures for trust registry and revocation lists
- Key rotation protocols with versioning
- Emergency revocation processes (T+0 to T+7 days)
- Verification procedures for partner workflows
- Monitoring & alerting setup
- File locations & permissions guide
- Quick reference commands
- Escalation contacts

## 2. Diligence FAQ
**Q1:** What evidence formats are required for MAND8 handoff?
**A1:** Portable verifier packets (ink.receipt.v2) with bundled evidence

**Q2:** How do we verify trust registry compliance?
**A2:** Through native Rust verification using ink.verification-report.v1

**Q3:** What security measures are in place?
**A3:** Trust boundary enforced via native verification, no JS-based trust

## 3. Verifier Instructions
- Accepts `ink_receipt.v2.json` + optional manifest/controls
- Requires trust registry/revocation list for strict verification
- Browser verifier available at `/verify/index.html`
- Native CLI command: `ink receipt --receipt ... --policy ...`

## 4. Security Posture
- Trust root: Native Rust verification
- No browser JavaScript trust
- Verification works offline
- Compliance with ink.receipt.v2 schema

## 5. Pilot Request
- Request template for insurance/MGA partners
- Includes verification workflow diagram
- Security assessment checklist
- Pilot success criteria