import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mand8 import authority, control, exposure, override, schema  # noqa: E402


def test_exposure_emission_and_event_trail() -> None:
    authority_receipt = authority.record(
        policy_ref="B1234UK2026",
        binder_ref="B1234UK2026",
        authority_id="auth-lma-binder-042",
        managing_agent="Lime Street Managing Agency Ltd",
        coverholder="North Dock Coverholder Ltd",
        case_id="case_lloyds_042",
    )
    risk_receipt = exposure.emit(
        exposure_unit_id="uk-cyber-eu-042",
        policy_ref="B1234UK2026",
        risk_class="cyber",
        insured_value=5000000.0,
        binder_ref="B1234UK2026",
        managing_agent="Lime Street Managing Agency Ltd",
        coverholder="North Dock Coverholder Ltd",
        authority_receipt=authority_receipt,
        case_id="case_lloyds_042",
    )
    risk_receipt = control.record(
        risk_receipt,
        control_id="ctl-model-drift-quarterly",
        control_name="Quarterly model drift review",
        status="pass",
        evidence_ref="ev-drift-review-q2-2026",
    )
    risk_receipt = override.record(
        risk_receipt,
        override_id="ovr-uk-042",
        override_type="no_manual_referral",
        reason="No manual referral required under binder terms.",
        overridden_by="system:no_override",
        effective_date="2026-07-16",
        outcome="not_required",
        human_review={
            "reviewer": "syndicate.underwriter@mand8.example",
            "notes": "London market review complete.",
            "status": "reviewed",
        },
    )

    event_types = [entry["event_type"] for entry in risk_receipt["event_trail"]]
    assert event_types == [
        "underwriting_action_emitted",
        "authority_receipt_recorded",
        "control_check_recorded",
        "override_recorded",
        "human_review_recorded",
    ]
    assert risk_receipt["case_id"] == "case_lloyds_042"
    assert all(entry["payload"]["case_id"] == "case_lloyds_042" for entry in risk_receipt["event_trail"])
    assert risk_receipt["domain_context"]["territory"] == "UK"
    assert risk_receipt["domain_context"]["market_segment"] == "lloyds_delegated_authority"
    assert risk_receipt["human_review"]["reviewer"] == "syndicate.underwriter@mand8.example"
    json.dumps(risk_receipt)
    assert schema.validate(risk_receipt) is True
