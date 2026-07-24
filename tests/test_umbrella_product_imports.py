from __future__ import annotations

import blkbxs
import due
import mand8
import mech_lab as ml

import blkbx_lab as bl


def test_blkbxs_reaches_the_root_public_runtime() -> None:
    assert blkbxs.demo is bl.demo
    assert blkbxs.verify is bl.verify
    assert blkbxs.InkReceiptResult is bl.InkReceiptResult


def test_mand8_public_api_and_packaged_assets_are_available() -> None:
    authority_receipt = mand8.authority.record(
        policy_ref="B1234UK2026",
        binder_ref="B1234UK2026",
        authority_id="auth-lma-binder-042",
        managing_agent="Lime Street Managing Agency Ltd",
    )
    risk_receipt = mand8.exposure.emit(
        exposure_unit_id="uk-cyber-eu-042",
        policy_ref="B1234UK2026",
        risk_class="cyber",
        insured_value=5000000.0,
        binder_ref="B1234UK2026",
        managing_agent="Lime Street Managing Agency Ltd",
        authority_receipt=authority_receipt,
        case_id=authority_receipt["case_id"],
    )
    underwriting_bundle = mand8.bundle.export(risk_receipt, authority_receipts=[authority_receipt])

    assert risk_receipt["schema"] == "mand8.risk_receipt.v1"
    assert authority_receipt["schema"] == "mand8.authority_receipt.v1"
    assert underwriting_bundle["schema"] == "mand8.bundle.v1"
    assert underwriting_bundle["case_id"] == risk_receipt["case_id"]
    assert mand8.schema.validate(authority_receipt) is True
    assert mand8.schema.validate(risk_receipt) is True
    assert mand8.schema.validate(underwriting_bundle, "mand8.bundle.v1") is True
    assert "underwriting_evidence_bundle.md" in mand8.bundle.available_templates()
    assert "Authority Receipt" in mand8.bundle.load_template("underwriting_evidence_bundle.md")
    assert len(mand8.scenarios.seeded_workspaces()) == 3


def test_due_public_api_and_packaged_assets_are_available() -> None:
    legal_receipt = due.receipt.create(
        domain_context={"product_surface": "contract-review-copilot"},
        event_type="legal_receipt_initialized",
        payload={"startup": "LexHarbor"},
    )
    legal_receipt = due.action.record(
        legal_receipt,
        action_name="draft_termination_notice",
        action_type="adverse_action",
        description="AI-assisted draft for a vendor termination notice.",
        legal_basis="Master services agreement section 11.2",
        materiality="high",
        adverse_action=True,
    )
    dispute_bundle = due.dispute.export(legal_receipt, audience="legal_ops")

    assert legal_receipt["schema"] == "due.legal_action_receipt.v1"
    assert dispute_bundle["schema"] == "due.dispute_bundle.v1"
    assert due.schema.validate(legal_receipt) is True
    assert due.schema.validate(dispute_bundle, "due.dispute_bundle.v1") is True
    assert "legal_defensibility_bundle.md" in due.bundle.available_templates()
    assert "matter context" in due.bundle.load_template("legal_defensibility_bundle.md").lower()


def test_mech_lab_compatibility_package_reexports_public_surfaces() -> None:
    assert ml.demo is bl.demo
    assert ml.mand8.receipt.create()["schema"] == "mand8.risk_receipt.v1"
    assert ml.due.receipt.create()["schema"] == "due.legal_action_receipt.v1"


def test_research_and_experimental_namespaces_report_extra_contract() -> None:
    research = bl.research.describe()
    experimental = bl.experimental.describe()

    assert research["extra"] == "research"
    assert research["dependencies"] == ["markdown_it"]
    assert research["modules"] == ["actuarial"]
    assert experimental["extra"] == "experimental"
    assert experimental["dependencies"] == ["rich"]
    assert ml.research.describe()["extra"] == "research"
    assert ml.experimental.describe()["extra"] == "experimental"
