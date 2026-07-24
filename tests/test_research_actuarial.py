from __future__ import annotations

import copy
import re
from pathlib import Path

from blkbx_lab.products.mand8 import authority, control, exposure
from blkbx_lab.research import actuarial


ROOT = Path(__file__).resolve().parents[1]


def test_mand8_case_annotation_contract_and_no_mutation() -> None:
    authority_receipt = authority.record(
        policy_ref="B1234UK2026",
        binder_ref="B1234UK2026",
        authority_id="auth-lma-binder-042",
        managing_agent="Lime Street Managing Agency Ltd",
        case_id="case_research_annotation_001",
        human_review={"reviewer": "underwriter@example.test", "status": "reviewed"},
    )
    risk_receipt = exposure.emit(
        exposure_unit_id="uk-cyber-eu-042",
        policy_ref="B1234UK2026",
        risk_class="cyber",
        insured_value=5000000.0,
        binder_ref="B1234UK2026",
        managing_agent="Lime Street Managing Agency Ltd",
        authority_receipt=authority_receipt,
        case_id="case_research_annotation_001",
        human_review={"reviewer": "underwriter@example.test", "status": "reviewed"},
    )
    risk_receipt = control.record(
        risk_receipt,
        control_id="ctrl_001",
        control_name="Human approval before bind",
        status="passed",
        evidence_ref="evidence/control-001.json",
    )
    original = copy.deepcopy(risk_receipt)

    annotation = actuarial.annotate_case(
        [risk_receipt, authority_receipt],
        verification_reports=[{"status": "passed", "report_ref": "verify/underwriting.json"}],
        computed_at="2026-07-20T00:00:00Z",
    )

    assert risk_receipt == original
    assert annotation["schema"] == "ink.actuarial_annotation.v1"
    assert annotation["status"] == "research_unvalidated"
    assert annotation["badge"] == "Research / unvalidated"
    assert annotation["engine"]["profile"] == "mand8_case_v1"
    assert annotation["annotates"]["case_id"] == "case_research_annotation_001"
    assert annotation["annotates"]["receipt_ids"] == [risk_receipt["receipt_id"], authority_receipt["receipt_id"]]
    assert all(item.startswith("sha256:") for item in annotation["annotates"]["receipt_hashes"])
    assert 0.0 <= annotation["completeness_score"] <= 1.0
    assert 0.0 <= annotation["defensibility_score"] <= 1.0
    assert annotation["evidence_penalty"] >= 1.0
    assert "integrity" not in annotation
    assert "signature" not in annotation
    assert any("not a reserve or capital formula" in item for item in annotation["limitations"])


def test_generic_receipt_annotation_reports_research_defects() -> None:
    incomplete = {
        "schema": "due.legal_action_receipt.v1",
        "receipt_id": "rcpt_incomplete",
        "issued_at": "not-a-timestamp",
        "event_trail": [],
    }

    annotation = actuarial.annotate_receipt(incomplete, computed_at="2026-07-20T00:00:00Z")
    defect_codes = {defect["code"] for defect in annotation["defects"]}

    assert annotation["engine"]["profile"] == "generic_receipt_v1"
    assert "missing_identity_coordinate" in defect_codes
    assert "invalid_timestamp" in defect_codes
    assert "missing_integrity_digest" in defect_codes
    assert "missing_verification_report" in defect_codes
    assert "absent_human_review" in defect_codes
    assert "missing_event_trail" in defect_codes
    assert "incomplete_domain_context" in defect_codes
    assert 0.0 <= annotation["completeness_score"] <= 1.0
    assert 0.0 <= annotation["defensibility_score"] <= 1.0
    assert "integrity" not in annotation
    assert "signature" not in annotation


def test_research_describe_exposes_actuarial_module() -> None:
    metadata = actuarial.describe()

    assert metadata["module"] == "blkbx_lab.research.actuarial"
    assert metadata["schema"] == "ink.actuarial_annotation.v1"
    assert metadata["annotation_integrity"] == "none"


def test_actuarial_terms_do_not_enter_receipt_field_ids() -> None:
    field_ids = (ROOT / "rust" / "crates" / "ink-core" / "src" / "field_ids.rs").read_text(encoding="utf-8").upper()

    for forbidden in ("ACTUARIAL", "COMPLETENESS", "DEFENSIBILITY", "RESERVE", "ADMISSIBILITY", "EVIDENCE_PENALTY"):
        assert re.search(rf"\b{forbidden}\b", field_ids) is None
