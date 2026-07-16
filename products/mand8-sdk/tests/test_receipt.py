import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mand8 import receipt, schema  # noqa: E402


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
    assert risk_receipt["integrity"]["signature_algorithm"] == "stub-v1"
    assert risk_receipt["integrity"]["signature"] is None
    assert risk_receipt["integrity"]["core_binding"] is None
    assert risk_receipt["integrity"]["digest"].startswith("sha256:")
    json.dumps(risk_receipt)
    assert schema.validate(risk_receipt) is True


def test_example_receipt_validates() -> None:
    example = json.loads(
        (Path(__file__).resolve().parents[1] / "examples" / "underwriting_receipt.json").read_text(encoding="utf-8")
    )
    assert schema.validate(example, "mand8.risk_receipt.v1") is True
