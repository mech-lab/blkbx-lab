from __future__ import annotations

import copy

import blkbxs


def test_smb_loan_demo_fixture_is_a_valid_ubr_graph() -> None:
    demo = blkbxs.scenarios.smb_loan_demo()
    receipts = demo["receipts"]
    validation = demo["graph_validation"]

    assert demo["generated_by"] == "blkbx_lab.products.blkbxs.scenarios.smb_loan_demo_fixture"
    assert demo["signature_policy"] == (
        "UBR-native synthetic proof values are intentionally omitted; "
        "Rails must issue ink.receipt.v2 companions before persistence."
    )
    assert len(receipts) == 8
    assert [receipt["operation"]["name"] for receipt in receipts] == [
        "consent.granted",
        "kyb.verified",
        "documents.received",
        "cashflow.analysis_completed",
        "ai.recommendation_generated",
        "human_credit_review.completed",
        "loan.application_decisioned",
        "conditional_approval_notice.generated",
    ]
    assert validation["valid"] is True
    assert validation["evidence_summary"]["available_to_verifier"] == 6
    assert validation["evidence_summary"]["committed_only"] == 2
    assert validation["ai_boundary_summary"]["valid"] is True
    assert all(blkbxs.schema.validate(receipt, "blkbxs.ubr.receipt.v1") for receipt in receipts)


def test_ubr_graph_validation_fails_for_missing_parent() -> None:
    demo = blkbxs.scenarios.smb_loan_demo()
    receipts = copy.deepcopy(demo["receipts"])
    receipts[1]["links"]["parent_receipts"] = ["urn:ubr:demo:missing-parent"]

    validation = blkbxs.ubr.validate_graph(receipts, evidence_manifest=demo["evidence_manifest"])

    assert validation["valid"] is False
    assert any(failure["code"] == "missing_parent" for failure in validation["failures"])


def test_ubr_graph_validation_fails_for_cross_process_parent() -> None:
    demo = blkbxs.scenarios.smb_loan_demo()
    receipts = copy.deepcopy(demo["receipts"])
    receipts[0]["operation"]["business_process_id"] = "urn:bank-process:loan-origination:OTHER"

    validation = blkbxs.ubr.validate_graph(receipts, evidence_manifest=demo["evidence_manifest"])

    assert validation["valid"] is False
    assert any(failure["code"] == "mixed_business_process" for failure in validation["failures"])
    assert any(failure["code"] == "cross_process_parent" for failure in validation["failures"])


def test_ubr_graph_validation_fails_for_cycle() -> None:
    demo = blkbxs.scenarios.smb_loan_demo()
    receipts = copy.deepcopy(demo["receipts"])
    receipts[0]["links"]["parent_receipts"] = [receipts[-1]["id"]]

    validation = blkbxs.ubr.validate_graph(receipts, evidence_manifest=demo["evidence_manifest"])

    assert validation["valid"] is False
    assert any(failure["code"] == "cycle_detected" for failure in validation["failures"])


def test_ubr_graph_validation_fails_for_duplicate_receipt_id() -> None:
    demo = blkbxs.scenarios.smb_loan_demo()
    receipts = copy.deepcopy(demo["receipts"])
    receipts[1]["id"] = receipts[0]["id"]

    validation = blkbxs.ubr.validate_graph(receipts, evidence_manifest=demo["evidence_manifest"])

    assert validation["valid"] is False
    assert any(failure["code"] == "duplicate_receipt_id" for failure in validation["failures"])


def test_ubr_bundle_export_is_schema_valid() -> None:
    demo = blkbxs.scenarios.smb_loan_demo()
    packet = blkbxs.bundle.export_ubr_graph(
        demo["receipts"],
        evidence_manifest=demo["evidence_manifest"],
        verifier_report=demo["verifier_report"],
    )

    assert packet["schema"] == "blkbxs.ubr.bundle.v1"
    assert packet["graph_validation"]["valid"] is True
    assert packet["verifier_report_summary"]["demo_only"] is True
    assert blkbxs.schema.validate(packet, "blkbxs.ubr.bundle.v1") is True


def test_blkbxs_public_facade_exposes_ubr_modules() -> None:
    assert blkbxs.ubr.SCHEMA_ID == "blkbxs.ubr.receipt.v1"
    assert blkbxs.bundle.BUNDLE_SCHEMA_ID == "blkbxs.ubr.bundle.v1"
    assert callable(blkbxs.scenarios.smb_loan_demo)
