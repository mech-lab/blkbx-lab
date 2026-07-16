# DUE SDK

DUE SDK makes AI actions legally defensible.

DUE SDK helps legaltech and legal-facing AI startups generate defensibility receipts from AI-assisted legal actions, matter context, authority checks, privilege decisions, disclosure events, human review, and dispute-relevant evidence.

DUE owns legal defensibility directly. It is not positioned as “MAND8 for legal.”

## Core Question

> Can this AI-assisted action survive dispute, discovery, privilege review, disclosure review, and liability scrutiny?

## API Surface

- `due.receipt.create()`
- `due.matter.bind()`
- `due.action.record()`
- `due.authority.check()`
- `due.privilege.record()`
- `due.disclosure.record()`
- `due.dispute.export()`
- `due.bundle.export()`
- `due.schema.validate()`

## Quickstart

```bash
cd products/due-sdk
pip install -e .
python examples/quickstart.py
```

```python
from due import action, authority, bundle, disclosure, dispute, matter, privilege, receipt, schema

record = receipt.create(
    domain_context={"product_surface": "contract-review-copilot"},
    event_type="legal_receipt_initialized",
    payload={"startup": "LexHarbor"},
)
record = action.record(
    record,
    action_name="draft_termination_notice",
    action_type="adverse_action",
    description="AI-assisted draft for a vendor termination notice.",
    legal_basis="Master services agreement section 11.2",
)
record = matter.bind(
    record,
    matter_id="matter-2026-042",
    jurisdiction="England and Wales",
    parties={"client": "LexHarbor", "counterparty": "North Bay Systems Ltd"},
    case_type="pre_dispute_contract",
)
record = authority.check(
    record,
    authority_id="auth-client-general-counsel",
    authority_name="General Counsel approval",
    jurisdiction="England and Wales",
    authority_type="internal_approval",
)
record = privilege.record(
    record,
    privilege_id="priv-2026-042",
    privilege_type="legal_advice",
    holder="LexHarbor",
    basis="Draft prepared for in-house legal review.",
)
record = disclosure.record(
    record,
    disclosure_id="disc-2026-042",
    disclosure_type="pre_action_exchange",
    recipient="North Bay Systems Ltd",
    content_summary="Approved outgoing notice only.",
    status="ready_if_required",
    human_review={
        "reviewer": "counsel@lexharbor.example",
        "notes": "Reviewed for privilege boundaries and disclosure scope.",
        "status": "reviewed",
    },
)

ready = dispute.export(record, audience="counsel")
schema.validate(record)
schema.validate(ready, "due.dispute_bundle.v1")
```

## Bundle Types

- Legal Defensibility Bundle
- Privilege Review Bundle
- Disclosure Evidence Bundle
- Litigation Hold Bundle
- AI Action Audit Trail
- Matter-Level Evidence Pack
- Dispute Readiness Bundle

## Product Verification

```bash
cd products/due-sdk
python -m pytest tests
```
