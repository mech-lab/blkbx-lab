# DUE API Surface

The shipped stable `due` import rides through `mechlab-sdk`. This source slice mirrors that surface for local development.

## Imports

```python
from due import action, authority, bundle, disclosure, dispute, matter, privilege, receipt, schema
```

## Core Calls

```python
receipt.create(domain_context=None, event_type="legal_action_receipt_created", payload=None, human_review=None)
action.record(receipt, action_name, action_type, description, legal_basis)
matter.bind(receipt, matter_id, jurisdiction, parties, case_type)
authority.check(receipt, authority_id, authority_name, jurisdiction, authority_type)
privilege.record(receipt, privilege_id, privilege_type, holder, basis)
disclosure.record(receipt, disclosure_id, disclosure_type, recipient, content_summary, status)
dispute.export(receipt, bundle_type="dispute_readiness_bundle", audience="counsel")
bundle.export(receipt, bundle_type="legal_defensibility_bundle", audience="counsel")
schema.validate(payload, schema_name=None)
```
