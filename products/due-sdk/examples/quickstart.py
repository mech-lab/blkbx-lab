from __future__ import annotations

import json
from pathlib import Path

from due import action, authority, disclosure, dispute, matter, privilege, receipt, schema


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    output_dir = Path("artifacts/due-defensibility")
    output_dir.mkdir(parents=True, exist_ok=True)

    record = receipt.create(
        domain_context={"product_surface": "contract-review-copilot"},
        event_type="legal_receipt_initialized",
        payload={"startup": "LexHarbor"},
    )
    record = action.record(
        record,
        action_name="draft_termination_notice",
        action_type="adverse_action",
        description="AI-assisted draft for a vendor termination notice.",
        legal_basis="Master services agreement section 11.2",
        materiality="high",
        adverse_action=True,
        chain_of_custody_ref="custody-2026-042",
    )
    record = matter.bind(
        record,
        matter_id="matter-2026-042",
        jurisdiction="England and Wales",
        parties={"client": "LexHarbor", "counterparty": "North Bay Systems Ltd"},
        case_type="pre_dispute_contract",
    )
    record = authority.check(
        record,
        authority_id="auth-client-general-counsel",
        authority_name="General Counsel approval",
        jurisdiction="England and Wales",
        authority_type="internal_approval",
        basis="Client sign-off before adverse action.",
    )
    record = privilege.record(
        record,
        privilege_id="priv-2026-042",
        privilege_type="legal_advice",
        holder="LexHarbor",
        basis="Draft prepared for in-house legal review.",
        scope="Internal legal workstream",
    )
    record = disclosure.record(
        record,
        disclosure_id="disc-2026-042",
        disclosure_type="pre_action_exchange",
        recipient="North Bay Systems Ltd",
        content_summary="Approved outgoing notice only.",
        status="ready_if_required",
        method="secure_portal",
        human_review={
            "reviewer": "counsel@lexharbor.example",
            "notes": "Reviewed for privilege boundaries and disclosure scope.",
            "status": "reviewed",
        },
    )
    ready = dispute.export(
        record,
        audience="counsel",
        notes="Readable by counsel, legal ops, compliance, or an accelerator reviewer.",
    )

    schema.validate(record)
    schema.validate(ready, "due.dispute_bundle.v1")

    _write_json(output_dir / "legal_action_receipt.json", record)
    _write_json(output_dir / "dispute_readiness_bundle.json", ready)
    print(output_dir)


if __name__ == "__main__":
    main()
