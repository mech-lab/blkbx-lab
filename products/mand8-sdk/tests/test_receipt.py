import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mand8 import authority, receipt, schema  # noqa: E402


def test_receipt_creation_and_integrity() -> None:
    risk_receipt = receipt.create(
        domain_context={
            "exposure_unit_id": "uk-cyber-eu-042",
            "policy_ref": "B1234UK2026",
            "risk_class": "cyber",
            "insured_value": 5000000.0,
            "currency": "GBP",
        }
    )
    assert risk_receipt["schema"] == "mand8.risk_receipt.v1"
    assert risk_receipt["case_id"].startswith("case_")
    assert risk_receipt["domain_context"]["case_id"] == risk_receipt["case_id"]
    assert risk_receipt["integrity"]["signature_algorithm"] == "stub-v1"
    assert risk_receipt["integrity"]["signature"] is None
    assert risk_receipt["integrity"]["core_binding"] is None
    assert risk_receipt["integrity"]["digest"].startswith("sha256:")
    json.dumps(risk_receipt)
    assert schema.validate(risk_receipt) is True


def test_authority_receipt_creation_and_linkable_event_payload() -> None:
    authority_receipt = authority.record(
        policy_ref="B1234UK2026",
        binder_ref="B1234UK2026",
        authority_id="auth-lma-binder-042",
        managing_agent="Lime Street Managing Agency Ltd",
        coverholder="North Dock Coverholder Ltd",
    )
    event_payload = authority.as_event_payload(authority_receipt)

    assert authority_receipt["schema"] == "mand8.authority_receipt.v1"
    assert authority_receipt["case_id"].startswith("case_")
    assert event_payload["receipt_id"] == authority_receipt["receipt_id"]
    assert event_payload["case_id"] == authority_receipt["case_id"]
    assert schema.validate(authority_receipt) is True


def test_example_receipt_validates() -> None:
    example = json.loads(
        (Path(__file__).resolve().parents[1] / "examples" / "underwriting_receipt.json").read_text(encoding="utf-8")
    )
    assert schema.validate(example, "mand8.risk_receipt.v1") is True
