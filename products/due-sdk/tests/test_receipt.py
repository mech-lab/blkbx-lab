import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from due import receipt, schema  # noqa: E402


def test_receipt_creation_and_integrity() -> None:
    legal_receipt = receipt.create(
        domain_context={"product_surface": "contract-review-copilot"},
        event_type="legal_receipt_initialized",
        payload={"startup": "LexHarbor"},
    )
    assert legal_receipt["schema"] == "due.legal_action_receipt.v1"
    assert legal_receipt["integrity"]["signature_algorithm"] == "stub-v1"
    assert legal_receipt["integrity"]["signature"] is None
    assert legal_receipt["integrity"]["core_binding"] is None
    assert legal_receipt["integrity"]["digest"].startswith("sha256:")
    json.dumps(legal_receipt)
    assert schema.validate(legal_receipt) is True


def test_example_receipt_validates() -> None:
    example = json.loads(
        (Path(__file__).resolve().parents[1] / "examples" / "legal_action_receipt.json").read_text(encoding="utf-8")
    )
    assert schema.validate(example, "due.legal_action_receipt.v1") is True
