"""BLKBXS UBR bundle export."""

from __future__ import annotations

from typing import Any

from .._common import clone, issued_at, new_identifier, stub_integrity
from .graph import business_process_id, validate_graph

BUNDLE_SCHEMA_ID = "blkbxs.ubr.bundle.v1"


def export_ubr_graph(
    receipts: list[dict[str, Any]],
    evidence_manifest: dict[str, Any] | None = None,
    verifier_report: dict[str, Any] | None = None,
    audience: str = "bank_credit_review",
) -> dict[str, Any]:
    validation = validate_graph(receipts, evidence_manifest=evidence_manifest, verifier_report=verifier_report)
    ordered_receipts = _ordered_receipts(receipts, validation["topological_order"])
    decision = _decision_summary(ordered_receipts, verifier_report)
    body = {
        "schema": BUNDLE_SCHEMA_ID,
        "bundle_id": f"bundle_{new_identifier('ubr')}",
        "business_process_id": validation["business_process_id"] or (business_process_id(receipts[0]) if receipts else ""),
        "bundle_type": "blkbxs_ubr_graph",
        "audience": audience,
        "generated_at": issued_at(),
        "graph_validation": validation,
        "graph_order": validation["topological_order"],
        "decision_summary": decision,
        "evidence_summary": validation["evidence_summary"],
        "ai_boundary_summary": validation["ai_boundary_summary"],
        "verifier_report_summary": _verifier_report_summary(verifier_report),
        "receipts": ordered_receipts,
        "evidence_manifest": evidence_manifest,
        "summary": (
            f"blkbxs_ubr_graph for {audience}: "
            f"{decision.get('application_id', 'unknown application')} "
            f"with {len(receipts)} receipt events"
        ),
    }
    bundle = clone(body)
    bundle["integrity"] = stub_integrity(body)
    return bundle


def _ordered_receipts(receipts: list[dict[str, Any]], order: list[str]) -> list[dict[str, Any]]:
    by_id = {receipt.get("id"): receipt for receipt in receipts}
    ordered = [by_id[receipt_id] for receipt_id in order if receipt_id in by_id]
    remaining = [receipt for receipt in receipts if receipt.get("id") not in set(order)]
    return clone({"receipts": [*ordered, *remaining]})["receipts"]


def _decision_summary(receipts: list[dict[str, Any]], verifier_report: dict[str, Any] | None) -> dict[str, Any]:
    report_decision = (verifier_report or {}).get("decision")
    if report_decision:
        return clone(report_decision)
    decision_receipt = next((receipt for receipt in receipts if receipt.get("operation", {}).get("name") == "loan.application_decisioned"), {})
    after = decision_receipt.get("state_transition", {}).get("after", {})
    return {
        "application_id": decision_receipt.get("state_transition", {}).get("subject", {}).get("id"),
        "status": after.get("application_status"),
        "amount": after.get("approved_amount"),
        "term_months": after.get("term_months"),
        "apr": after.get("interest_rate", {}).get("apr") or after.get("apr"),
        "conditions": after.get("conditions", []),
    }


def _verifier_report_summary(verifier_report: dict[str, Any] | None) -> dict[str, Any] | None:
    if not verifier_report:
        return None
    return {
        "report_id": verifier_report.get("report_id"),
        "generated_at": verifier_report.get("generated_at"),
        "summary": verifier_report.get("summary", {}),
        "limitations": verifier_report.get("limitations", []),
        "demo_only": True,
    }


__all__ = ["BUNDLE_SCHEMA_ID", "export_ubr_graph"]
