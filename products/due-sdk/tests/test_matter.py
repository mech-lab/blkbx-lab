import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from due import action, authority, disclosure, matter, privilege, receipt, schema  # noqa: E402


def test_matter_binding_authority_privilege_and_human_review_flow() -> None:
    legal_receipt = receipt.create(
        domain_context={"product_surface": "contract-review-copilot"},
        event_type="legal_receipt_initialized",
        payload={"startup": "LexHarbor"},
    )
    legal_receipt = action.record(
        legal_receipt,
        action_name="draft_termination_notice",
        action_type="adverse_action",
        description="AI-assisted draft for a vendor termination notice.",
        legal_basis="Master services agreement section 11.2",
        materiality="high",
        adverse_action=True,
    )
    legal_receipt = matter.bind(
        legal_receipt,
        matter_id="matter-2026-042",
        jurisdiction="England and Wales",
        parties={"client": "LexHarbor", "counterparty": "North Bay Systems Ltd"},
        case_type="pre_dispute_contract",
    )
    legal_receipt = authority.check(
        legal_receipt,
        authority_id="auth-client-general-counsel",
        authority_name="General Counsel approval",
        jurisdiction="England and Wales",
        authority_type="internal_approval",
    )
    legal_receipt = privilege.record(
        legal_receipt,
        privilege_id="priv-2026-042",
        privilege_type="legal_advice",
        holder="LexHarbor",
        basis="Draft prepared for in-house legal review.",
    )
    legal_receipt = disclosure.record(
        legal_receipt,
        disclosure_id="disc-2026-042",
        disclosure_type="pre_action_exchange",
        recipient="North Bay Systems Ltd",
        content_summary="Approved outgoing notice only.",
        status="ready_if_required",
        human_review={
            "reviewer": "counsel@lexharbor.example",
            "notes": "Reviewed for privilege boundaries and disclosure scope.",
            "status": "reviewed",
        },
    )

    event_types = [entry["event_type"] for entry in legal_receipt["event_trail"]]
    assert event_types == [
        "legal_receipt_initialized",
        "ai_assisted_legal_action_recorded",
        "matter_bound",
        "authority_checked",
        "privilege_recorded",
        "disclosure_recorded",
        "human_review_recorded",
    ]
    assert legal_receipt["domain_context"]["matter_id"] == "matter-2026-042"
    assert legal_receipt["human_review"]["reviewer"] == "counsel@lexharbor.example"
    json.dumps(legal_receipt)
    assert schema.validate(legal_receipt) is True
