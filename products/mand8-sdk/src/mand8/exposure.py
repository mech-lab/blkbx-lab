"""MAND8 exposure-unit receipts."""

from __future__ import annotations

from typing import Any

from .receipt import append_event, create


def emit(
    exposure_unit_id: str,
    policy_ref: str,
    risk_class: str,
    insured_value: float,
    currency: str = "GBP",
    territory: str = "UK",
    market_segment: str = "lloyds_delegated_authority",
    binder_ref: str | None = None,
    managing_agent: str | None = None,
    coverholder: str | None = None,
    authority_receipt: dict[str, Any] | None = None,
    control_check: dict[str, Any] | None = None,
    override_state: dict[str, Any] | None = None,
    policy_conditions: list[str] | None = None,
    exclusions: list[str] | None = None,
    human_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    domain_context = {
        "exposure_unit_id": exposure_unit_id,
        "policy_ref": policy_ref,
        "risk_class": risk_class,
        "insured_value": insured_value,
        "currency": currency,
        "territory": territory,
        "market_segment": market_segment,
        "binder_ref": binder_ref,
        "managing_agent": managing_agent,
        "coverholder": coverholder,
        "policy_conditions": policy_conditions or [],
        "exclusions": exclusions or [],
        "regulators": ["FCA", "PRA"] if territory == "UK" else [],
    }
    receipt = create(
        domain_context=domain_context,
        event_type="underwriting_action_emitted",
        payload={
            "action": "ai_underwriting_action",
            "exposure_unit_id": exposure_unit_id,
            "policy_ref": policy_ref,
        },
    )
    if authority_receipt:
        receipt = append_event(receipt, "authority_receipt_recorded", authority_receipt)
    if control_check:
        receipt = append_event(receipt, "control_check_recorded", control_check)
    if override_state:
        receipt = append_event(
            receipt,
            "override_recorded",
            override_state,
            human_review=human_review,
        )
    elif human_review:
        receipt = append_event(receipt, "portfolio_review_noted", {}, human_review=human_review)
    return receipt
