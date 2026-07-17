# MAND8 API Surface

The shipped stable `mand8` import rides through `mechlab-sdk`. This source slice mirrors that surface for local development.

## Imports

```python
from mand8 import bundle, control, exposure, incident, override, receipt, schema
```

## Core Constructors

```python
receipt.create(
    domain_context=None,
    event_type="receipt_created",
    payload=None,
    human_review=None,
)
```

```python
exposure.emit(
    exposure_unit_id,
    policy_ref,
    risk_class,
    insured_value,
    currency="GBP",
    territory="UK",
    market_segment="lloyds_delegated_authority",
    binder_ref=None,
    managing_agent=None,
    coverholder=None,
    authority_receipt=None,
    control_check=None,
    override_state=None,
    policy_conditions=None,
    exclusions=None,
    human_review=None,
)
```

```python
control.record(receipt, control_id, control_name, status, evidence_ref="", control_type="risk_control")
incident.record(receipt, incident_id, incident_type, severity, description)
override.record(receipt, override_id, override_type, reason, overridden_by, effective_date)
bundle.export(receipt, bundle_type="underwriting_evidence_bundle", audience="lloyds_underwriter")
schema.validate(payload, schema_name=None)
```
