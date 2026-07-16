# MAND8 SDK

MAND8 SDK makes AI risk insurable.

MAND8 SDK helps insurance-facing AI startups generate underwriter-ready risk receipts from AI actions, model decisions, controls, incidents, overrides, and exposure units so those systems can support pricing, monitoring, renewals, claims review, exclusions, and policy-condition evidence.

MAND8 is UK-first by design. Delegated authority is a Lloyd's-native construct. The Authority Receipt maps onto the binder logic that London market managing agents already operate, audit, and defend to the FCA and PRA. This is not an American product retro-fitted for the UK. It starts here.

## API Surface

- `mand8.receipt.create()`
- `mand8.exposure.emit()`
- `mand8.control.record()`
- `mand8.incident.record()`
- `mand8.override.record()`
- `mand8.bundle.export()`
- `mand8.schema.validate()`

## Quickstart

```bash
cd products/mand8-sdk
pip install -e .
python examples/quickstart.py
```

```python
from mand8 import bundle, control, exposure, override, schema

receipt = exposure.emit(
    exposure_unit_id="uk-cyber-eu-042",
    policy_ref="B1234UK2026",
    risk_class="cyber",
    insured_value=5000000.0,
    currency="GBP",
    binder_ref="B1234UK2026",
    managing_agent="Lime Street Managing Agency Ltd",
    coverholder="North Dock Coverholder Ltd",
    authority_receipt={
        "authority_id": "auth-lma-binder-042",
        "construct": "delegated_authority",
        "lloyds_binding_ref": "B1234UK2026",
        "regulators": ["FCA", "PRA"],
    },
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
    human_review={
        "reviewer": "syndicate.underwriter@mand8.example",
        "notes": "Delegated authority terms satisfied and London market review complete.",
        "status": "reviewed",
    },
)

pack = bundle.export(
    receipt,
    bundle_type="underwriting_evidence_bundle",
    audience="lloyds_underwriter",
)

schema.validate(receipt)
schema.validate(pack, "mand8.bundle.v1")
```

## Bundle Types

- Underwriting Evidence Bundle
- Claims Defensibility Bundle
- Renewal Evidence Pack
- Actuarial Signal Export
- Policy-Condition Evidence Trail
- Risk-Control Monitoring Receipt

## Product Verification

```bash
cd products/mand8-sdk
python -m pytest tests
```
