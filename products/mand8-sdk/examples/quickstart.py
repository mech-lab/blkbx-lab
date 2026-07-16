from __future__ import annotations

import json
from pathlib import Path

from mand8 import bundle, control, exposure, override, schema


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    output_dir = Path("artifacts/mand8-uk-first")
    output_dir.mkdir(parents=True, exist_ok=True)

    receipt = exposure.emit(
        exposure_unit_id="uk-cyber-eu-042",
        policy_ref="B1234UK2026",
        risk_class="cyber",
        insured_value=5000000.0,
        currency="GBP",
        binder_ref="B1234UK2026",
        managing_agent="Lime Street Managing Agency Ltd",
        coverholder="North Dock Coverholder Ltd",
        authority_receipt={
            "authority_id": "auth-lma-binder-042",
            "construct": "delegated_authority",
            "lloyds_binding_ref": "B1234UK2026",
            "managing_agent": "Lime Street Managing Agency Ltd",
            "coverholder": "North Dock Coverholder Ltd",
            "regulators": ["FCA", "PRA"],
        },
        policy_conditions=[
            "Quarterly model drift review",
            "Human referral on confidence below threshold",
        ],
        exclusions=[
            "Silent cyber outside declared products",
        ],
    )
    receipt = control.record(
        receipt,
        control_id="ctl-model-drift-quarterly",
        control_name="Quarterly model drift review",
        status="pass",
        evidence_ref="ev-drift-review-q2-2026",
    )
    receipt = override.record(
        receipt,
        override_id="ovr-uk-042",
        override_type="no_manual_referral",
        reason="No manual referral required under binder terms.",
        overridden_by="system:no_override",
        effective_date="2026-07-16",
        outcome="not_required",
        human_review={
            "reviewer": "syndicate.underwriter@mand8.example",
            "notes": "Delegated authority terms satisfied and London market review complete.",
            "status": "reviewed",
        },
    )
    pack = bundle.export(
        receipt,
        bundle_type="underwriting_evidence_bundle",
        audience="lloyds_underwriter",
        notes="Readable by a managing agent, MGA, reinsurer, or accelerator reviewer.",
    )

    schema.validate(receipt)
    schema.validate(pack, "mand8.bundle.v1")

    _write_json(output_dir / "underwriting_receipt.json", receipt)
    _write_json(output_dir / "underwriting_evidence_bundle.json", pack)
    print(output_dir)


if __name__ == "__main__":
    main()
