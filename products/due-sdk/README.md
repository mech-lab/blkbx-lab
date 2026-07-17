# DUE SDK Source Slice

DUE makes AI actions legally defensible.

This directory is an in-repo source slice for the legal-facing DUE surface. The currently shipped stable `due` Python import rides through the root `mechlab-sdk` wheel rather than a separately published package.

## Shipped Import Path

```bash
pip install --pre mechlab-sdk
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
)

ready = dispute.export(record, audience="counsel")
schema.validate(record)
schema.validate(ready, "due.dispute_bundle.v1")
```

## Local Slice Workflow

For source-slice development inside this repository:

```bash
cd products/due-sdk
pip install -e .
python examples/quickstart.py
```

## Related Docs

- [API surface](docs/api-surface.md)
- [Developer positioning](docs/developer-positioning.md)
- [Legal domain model](docs/legal-domain-model.md)
- [Application slice note](docs/legaltech-application-slice.md)
