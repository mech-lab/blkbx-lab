import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from due import bundle, dispute, receipt, schema  # noqa: E402


def test_bundle_and_dispute_exports() -> None:
    legal_receipt = receipt.create(
        domain_context={"product_surface": "contract-review-copilot", "matter_id": "matter-2026-042"},
        event_type="legal_receipt_initialized",
        payload={"startup": "LexHarbor"},
    )
    defensibility_bundle = bundle.export(
        legal_receipt,
        bundle_type="legal_defensibility_bundle",
        audience="counsel",
    )
    readiness_bundle = dispute.export(
        legal_receipt,
        audience="legal_ops",
    )

    assert defensibility_bundle["schema"] == "due.dispute_bundle.v1"
    assert readiness_bundle["schema"] == "due.dispute_bundle.v1"
    assert "counsel" in bundle.summarize(defensibility_bundle)
    assert schema.validate(defensibility_bundle, "due.dispute_bundle.v1") is True
    assert schema.validate(readiness_bundle, "due.dispute_bundle.v1") is True
    json.dumps(defensibility_bundle)


def test_example_bundle_validates() -> None:
    example = json.loads(
        (Path(__file__).resolve().parents[1] / "examples" / "dispute_defensibility_bundle.json").read_text(
            encoding="utf-8"
        )
    )
    assert schema.validate(example, "due.dispute_bundle.v1") is True
