"""Seeded Lloyd's Labs demo scenarios for MAND8."""

from __future__ import annotations

from typing import Any

from .._common import clone
from . import authority, bundle, control, exposure, incident, override
from .receipt import refresh_integrity


def _with_issued_at(document: dict[str, Any], issued_at: str, reviewed_at: str | None = None) -> dict[str, Any]:
    frozen = clone(document)
    frozen["issued_at"] = issued_at
    if reviewed_at and frozen.get("human_review", {}).get("status") != "not_reviewed":
        frozen["human_review"]["reviewed_at"] = reviewed_at
        for entry in frozen.get("event_trail", []):
            if entry.get("event_type") == "human_review_recorded":
                entry.setdefault("payload", {})["reviewed_at"] = reviewed_at
    return refresh_integrity(frozen)


def _scenario_happy_path() -> dict[str, Any]:
    case_id = "case_mand8_lloyds_happy_001"
    authority_receipt = authority.record(
        policy_ref="B1234UK2026",
        binder_ref="B1234UK2026",
        authority_id="auth-lma-binder-042",
        managing_agent="Lime Street Managing Agency Ltd",
        coverholder="North Dock Coverholder Ltd",
        permitted_risk_classes=["cyber"],
        controls_required=["Quarterly model drift review"],
        policy_conditions=["Human referral on confidence below threshold"],
        exclusions=["Silent cyber outside declared products"],
        human_review={
            "reviewer": "syndicate.underwriter@mand8.example",
            "notes": "Delegated authority terms confirmed for the binder.",
            "status": "reviewed",
            "reviewed_at": "2026-07-17T09:03:00Z",
        },
        case_id=case_id,
        receipt_id="arcpt_happy_001",
        action_id="act_authority_happy_001",
    )
    risk_receipt = exposure.emit(
        exposure_unit_id="uk-cyber-eu-042",
        policy_ref="B1234UK2026",
        risk_class="cyber",
        insured_value=5000000.0,
        currency="GBP",
        binder_ref="B1234UK2026",
        managing_agent="Lime Street Managing Agency Ltd",
        coverholder="North Dock Coverholder Ltd",
        authority_receipt=authority_receipt,
        policy_conditions=[
            "Quarterly model drift review",
            "Human referral on confidence below threshold",
        ],
        exclusions=["Silent cyber outside declared products"],
        case_id=case_id,
    )
    risk_receipt = control.record(
        risk_receipt,
        control_id="ctl-model-drift-quarterly",
        control_name="Quarterly model drift review",
        status="pass",
        evidence_ref="ev-drift-review-q2-2026",
        details={"review_window": "2026-Q2"},
    )
    risk_receipt = override.record(
        risk_receipt,
        override_id="ovr-uk-042",
        override_type="no_manual_referral",
        reason="No manual referral required under binder terms.",
        overridden_by="system:no_override",
        effective_date="2026-07-17",
        outcome="not_required",
        details={"confidence_floor_met": True},
        human_review={
            "reviewer": "syndicate.underwriter@mand8.example",
            "notes": "Delegated authority terms satisfied and London market review complete.",
            "status": "reviewed",
            "reviewed_at": "2026-07-17T09:05:00Z",
        },
    )
    risk_receipt = _with_issued_at(risk_receipt, "2026-07-17T09:00:00Z", "2026-07-17T09:05:00Z")
    authority_receipt = _with_issued_at(authority_receipt, "2026-07-17T09:02:00Z", "2026-07-17T09:03:00Z")
    renewal_bundle = bundle.export(
        risk_receipt,
        bundle_type="underwriting_evidence_bundle",
        audience="lloyds_underwriter",
        notes="Canonical Lloyd's cyber delegated-authority case.",
        authority_receipts=[authority_receipt],
        verification_reports=[
            {"status": "passed", "report_ref": "verify/happy-path-report.json"},
        ],
    )
    renewal_bundle = clone(renewal_bundle)
    renewal_bundle["generated_at"] = "2026-07-17T09:07:00Z"
    renewal_bundle = refresh_integrity(renewal_bundle)
    return {
        "workspace": {
            "name": "Lloyd's Cyber Happy Path",
            "slug": "mand8-lloyds-cyber-happy-path",
            "product_type": "mand8",
        },
        "scenario": "happy_path",
        "case_id": case_id,
        "primary_receipt": risk_receipt,
        "authority_receipts": [authority_receipt],
        "incident_receipts": [],
        "bundle": renewal_bundle,
        "review_request": {
            "title": "Lloyd's underwriter review",
            "reviewer_role": "lloyds_underwriter",
            "shared_bundle_name": "Lloyd's cyber happy-path portal",
        },
    }


def _scenario_human_review_edge() -> dict[str, Any]:
    case_id = "case_mand8_lloyds_review_002"
    authority_receipt = authority.record(
        policy_ref="B2234UK2026",
        binder_ref="B2234UK2026",
        authority_id="auth-lma-binder-2234",
        managing_agent="Lime Street Managing Agency Ltd",
        coverholder="North Dock Coverholder Ltd",
        permitted_risk_classes=["cyber"],
        controls_required=["Quarterly human referral calibration"],
        human_review={
            "reviewer": "managing.agent@mand8.example",
            "notes": "Borderline confidence score requires underwriter review before binding.",
            "status": "reviewed",
            "reviewed_at": "2026-07-17T10:02:00Z",
        },
        case_id=case_id,
        receipt_id="arcpt_review_002",
        action_id="act_authority_review_002",
    )
    risk_receipt = exposure.emit(
        exposure_unit_id="uk-cyber-eu-2234",
        policy_ref="B2234UK2026",
        risk_class="cyber",
        insured_value=3200000.0,
        binder_ref="B2234UK2026",
        managing_agent="Lime Street Managing Agency Ltd",
        coverholder="North Dock Coverholder Ltd",
        authority_receipt=authority_receipt,
        case_id=case_id,
    )
    risk_receipt = control.record(
        risk_receipt,
        control_id="ctl-human-referral-calibration",
        control_name="Quarterly human referral calibration",
        status="pass",
        evidence_ref="ev-human-referral-calibration-q3-2026",
    )
    risk_receipt = override.record(
        risk_receipt,
        override_id="ovr-review-2234",
        override_type="manual_referral",
        reason="Human review required because loss-history signal breached the referral floor.",
        overridden_by="syndicate.underwriter@mand8.example",
        effective_date="2026-07-17",
        outcome="manual_referral_required",
        human_review={
            "reviewer": "syndicate.underwriter@mand8.example",
            "notes": "Binding paused pending manual market review.",
            "status": "reviewed",
            "reviewed_at": "2026-07-17T10:05:00Z",
        },
    )
    risk_receipt = _with_issued_at(risk_receipt, "2026-07-17T10:00:00Z", "2026-07-17T10:05:00Z")
    authority_receipt = _with_issued_at(authority_receipt, "2026-07-17T10:01:00Z", "2026-07-17T10:02:00Z")
    review_bundle = bundle.export(
        risk_receipt,
        bundle_type="underwriting_evidence_bundle",
        audience="lloyds_underwriter",
        notes="Edge case with explicit human referral and underwriter hold.",
        authority_receipts=[authority_receipt],
        verification_reports=[
            {"status": "passed", "report_ref": "verify/human-review-edge-report.json"},
        ],
    )
    review_bundle = clone(review_bundle)
    review_bundle["generated_at"] = "2026-07-17T10:06:00Z"
    review_bundle = refresh_integrity(review_bundle)
    return {
        "workspace": {
            "name": "Lloyd's Human Review Edge Case",
            "slug": "mand8-lloyds-human-review-edge",
            "product_type": "mand8",
        },
        "scenario": "human_review_edge",
        "case_id": case_id,
        "primary_receipt": risk_receipt,
        "authority_receipts": [authority_receipt],
        "incident_receipts": [],
        "bundle": review_bundle,
        "review_request": {
            "title": "Manual referral review",
            "reviewer_role": "lloyds_underwriter",
            "shared_bundle_name": "Lloyd's human-review portal",
        },
    }


def _scenario_incident_to_renewal() -> dict[str, Any]:
    case_id = "case_mand8_lloyds_incident_003"
    authority_receipt = authority.record(
        policy_ref="B3234UK2026",
        binder_ref="B3234UK2026",
        authority_id="auth-lma-binder-3234",
        managing_agent="Lime Street Managing Agency Ltd",
        coverholder="North Dock Coverholder Ltd",
        permitted_risk_classes=["cyber"],
        controls_required=["Monthly anomaly monitoring"],
        case_id=case_id,
        receipt_id="arcpt_incident_003",
        action_id="act_authority_incident_003",
    )
    risk_receipt = exposure.emit(
        exposure_unit_id="uk-cyber-eu-3234",
        policy_ref="B3234UK2026",
        risk_class="cyber",
        insured_value=2800000.0,
        binder_ref="B3234UK2026",
        managing_agent="Lime Street Managing Agency Ltd",
        coverholder="North Dock Coverholder Ltd",
        authority_receipt=authority_receipt,
        case_id=case_id,
    )
    risk_receipt = control.record(
        risk_receipt,
        control_id="ctl-monthly-anomaly-monitor",
        control_name="Monthly anomaly monitoring",
        status="pass",
        evidence_ref="ev-monthly-anomaly-monitor-2026-07",
    )
    risk_receipt = incident.record(
        risk_receipt,
        incident_id="inc-3234-01",
        incident_type="drift_alert",
        severity="medium",
        description="Model drift alert triggered during post-bind monitoring.",
        claims_impact="monitor_for_renewal",
        resolution={
            "outcome": "monitoring_intensified",
            "next_review_at": "2026-08-01",
        },
        human_review={
            "reviewer": "portfolio.actuary@mand8.example",
            "notes": "Incident accepted into renewal monitoring pack.",
            "status": "reviewed",
            "reviewed_at": "2026-07-17T11:04:00Z",
        },
    )
    incident_receipt = {
        "schema": "mand8.incident_receipt.v1",
        "case_id": case_id,
        "incident_id": "inc-3234-01",
        "incident_type": "drift_alert",
        "severity": "medium",
        "description": "Model drift alert triggered during post-bind monitoring.",
        "claims_impact": "monitor_for_renewal",
        "resolution": {
            "outcome": "monitoring_intensified",
            "next_review_at": "2026-08-01",
        },
    }
    risk_receipt = _with_issued_at(risk_receipt, "2026-07-17T11:00:00Z", "2026-07-17T11:04:00Z")
    authority_receipt = _with_issued_at(authority_receipt, "2026-07-17T11:01:00Z")
    renewal_bundle = bundle.export(
        risk_receipt,
        bundle_type="renewal_evidence_pack",
        audience="carrier_innovation_team",
        notes="Incident-to-renewal edge case with explicit monitoring escalation.",
        authority_receipts=[authority_receipt],
        incident_receipts=[incident_receipt],
        verification_reports=[
            {"status": "passed", "report_ref": "verify/incident-renewal-report.json"},
            {"status": "warning", "report_ref": "verify/incident-renewal-monitoring.json"},
        ],
    )
    renewal_bundle = clone(renewal_bundle)
    renewal_bundle["generated_at"] = "2026-07-17T11:06:00Z"
    renewal_bundle = refresh_integrity(renewal_bundle)
    return {
        "workspace": {
            "name": "Lloyd's Incident To Renewal",
            "slug": "mand8-lloyds-incident-renewal-edge",
            "product_type": "mand8",
        },
        "scenario": "incident_to_renewal",
        "case_id": case_id,
        "primary_receipt": risk_receipt,
        "authority_receipts": [authority_receipt],
        "incident_receipts": [incident_receipt],
        "bundle": renewal_bundle,
        "review_request": {
            "title": "Renewal monitoring review",
            "reviewer_role": "carrier_innovation_team",
            "shared_bundle_name": "Lloyd's incident-renewal portal",
        },
    }


SCENARIO_BUILDERS = {
    "lloyds_cyber_happy_path": _scenario_happy_path,
    "lloyds_human_review_edge_case": _scenario_human_review_edge,
    "lloyds_human_review_edge": _scenario_human_review_edge,
    "lloyds_incident_to_renewal": _scenario_incident_to_renewal,
}


def available_scenarios() -> list[str]:
    return sorted(name for name in SCENARIO_BUILDERS if name != "lloyds_human_review_edge")


def build_scenario(name: str) -> dict[str, Any]:
    builder = SCENARIO_BUILDERS.get(name)
    if builder is None:
        raise ValueError(f"Unknown MAND8 scenario: {name}")
    return builder()


def seeded_workspaces() -> list[dict[str, Any]]:
    return [build_scenario(name) for name in available_scenarios()]


__all__ = ["available_scenarios", "build_scenario", "seeded_workspaces"]
