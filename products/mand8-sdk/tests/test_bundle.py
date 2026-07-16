import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mand8 import bundle, exposure, schema  # noqa: E402


def test_underwriting_and_renewal_bundle_exports() -> None:
    risk_receipt = exposure.emit(
        exposure_unit_id="uk-cyber-eu-042",
        policy_ref="B1234UK2026",
        risk_class="cyber",
        insured_value=5000000.0,
        binder_ref="B1234UK2026",
        managing_agent="Lime Street Managing Agency Ltd",
    )
    underwriting_bundle = bundle.export(
        risk_receipt,
        bundle_type="underwriting_evidence_bundle",
        audience="lloyds_underwriter",
    )
    renewal_bundle = bundle.export(
        risk_receipt,
        bundle_type="renewal_evidence_pack",
        audience="carrier_innovation_team",
    )

    assert underwriting_bundle["schema"] == "mand8.bundle.v1"
    assert renewal_bundle["schema"] == "mand8.bundle.v1"
    assert "lloyds_underwriter" in bundle.summarize(underwriting_bundle)
    assert schema.validate(underwriting_bundle, "mand8.bundle.v1") is True
    assert schema.validate(renewal_bundle, "mand8.bundle.v1") is True
    json.dumps(underwriting_bundle)


def test_example_bundle_validates() -> None:
    example = json.loads(
        (Path(__file__).resolve().parents[1] / "examples" / "renewal_evidence_pack.json").read_text(encoding="utf-8")
    )
    assert schema.validate(example, "mand8.bundle.v1") is True
