import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mand8 import authority, bundle, exposure, schema, scenarios  # noqa: E402


def test_underwriting_and_renewal_bundle_exports() -> None:
    authority_receipt = authority.record(
        policy_ref="B1234UK2026",
        binder_ref="B1234UK2026",
        authority_id="auth-lma-binder-042",
        managing_agent="Lime Street Managing Agency Ltd",
        coverholder="North Dock Coverholder Ltd",
        case_id="case_lloyds_bundle_001",
    )
    risk_receipt = exposure.emit(
        exposure_unit_id="uk-cyber-eu-042",
        policy_ref="B1234UK2026",
        risk_class="cyber",
        insured_value=5000000.0,
        binder_ref="B1234UK2026",
        managing_agent="Lime Street Managing Agency Ltd",
        authority_receipt=authority_receipt,
        case_id="case_lloyds_bundle_001",
    )
    underwriting_bundle = bundle.export(
        risk_receipt,
        bundle_type="underwriting_evidence_bundle",
        audience="lloyds_underwriter",
        authority_receipts=[authority_receipt],
        verification_reports=[{"status": "passed", "report_ref": "verify/underwriting.json"}],
    )
    renewal_bundle = bundle.export(
        risk_receipt,
        bundle_type="renewal_evidence_pack",
        audience="carrier_innovation_team",
        authority_receipts=[authority_receipt],
    )

    assert underwriting_bundle["schema"] == "mand8.bundle.v1"
    assert renewal_bundle["schema"] == "mand8.bundle.v1"
    assert underwriting_bundle["case_id"] == "case_lloyds_bundle_001"
    assert underwriting_bundle["related_receipts"]["authority_receipt_ids"] == [authority_receipt["receipt_id"]]
    assert underwriting_bundle["coverage_summary"]["authority_receipt_count"] == 1
    assert "lloyds_underwriter" in bundle.summarize(underwriting_bundle)
    assert schema.validate(underwriting_bundle, "mand8.bundle.v1") is True
    assert schema.validate(renewal_bundle, "mand8.bundle.v1") is True
    json.dumps(underwriting_bundle)


def test_seeded_scenarios_provide_three_demo_workspaces() -> None:
    seeded = scenarios.seeded_workspaces()

    assert [item["scenario"] for item in seeded] == [
        "happy_path",
        "human_review_edge",
        "incident_to_renewal",
    ]
    assert seeded[0]["bundle"]["coverage_summary"]["authority_receipt_count"] == 1
    assert seeded[2]["bundle"]["coverage_summary"]["incident_receipt_count"] == 1


def test_example_bundle_validates() -> None:
    example = json.loads(
        (Path(__file__).resolve().parents[1] / "examples" / "renewal_evidence_pack.json").read_text(encoding="utf-8")
    )
    assert schema.validate(example, "mand8.bundle.v1") is True
