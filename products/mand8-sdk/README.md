# MAND8 SDK Source Slice

MAND8 makes AI risk insurable.

This directory is an in-repo source slice for the insurance-facing MAND8 surface. The currently shipped stable `mand8` Python import rides through the root `mechlab-sdk` wheel rather than a separately published package.

## Shipped Import Path

```bash
pip install --pre mechlab-sdk
```

```python
from mand8 import authority, bundle, control, exposure, override, schema

authority_receipt = authority.record(
    policy_ref="B1234UK2026",
    binder_ref="B1234UK2026",
    authority_id="auth-lma-binder-042",
    managing_agent="Lime Street Managing Agency Ltd",
    coverholder="North Dock Coverholder Ltd",
)

receipt = exposure.emit(
    exposure_unit_id="uk-cyber-eu-042",
    policy_ref="B1234UK2026",
    risk_class="cyber",
    insured_value=5000000.0,
    currency="GBP",
    binder_ref="B1234UK2026",
    managing_agent="Lime Street Managing Agency Ltd",
    coverholder="North Dock Coverholder Ltd",
    authority_receipt=authority_receipt,
)

receipt = control.record(
    receipt,
    control_id="ctl-model-drift-quarterly",
    control_name="Quarterly model drift review",
    status="pass",
    evidence_ref="ev-drift-review-q2-2026",
)

receipt = override.record(
    receipt,
    override_id="ovr-uk-042",
    override_type="no_manual_referral",
    reason="No manual referral required under binder terms.",
    overridden_by="system:no_override",
    effective_date="2026-07-16",
)

pack = bundle.export(
    receipt,
    bundle_type="underwriting_evidence_bundle",
    audience="lloyds_underwriter",
)

schema.validate(receipt)
schema.validate(pack, "mand8.bundle.v1")
```

## Public API Surface

- `mand8.exposure.emit()`
- `mand8.authority.record()`
- `mand8.control.record()`
- `mand8.override.record()`
- `mand8.incident.record()`
- `mand8.bundle.export()`
- `mand8.schema.validate()`

## Local Slice Workflow

For source-slice development inside this repository:

```bash
cd products/mand8-sdk
pip install -e .
python examples/quickstart.py
```

## Lloyd's Labs Demo

The fixed Friday, July 17, 2026 Lloyd's Labs scenarios are:

- `lloyds_cyber_happy_path`
- `lloyds_human_review_edge_case`
- `lloyds_incident_to_renewal`

The full demo runbook lives in [../../docs/mand8-lloyds-labs-demo.md](../../docs/mand8-lloyds-labs-demo.md).

## Related Docs

- [API surface](docs/api-surface.md)
- [Developer positioning](docs/developer-positioning.md)
- [Insurance domain model](docs/insurance-domain-model.md)
- [Application slice note](docs/northwestern-application-slice.md)
