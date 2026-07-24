"""Graph validation helpers for BLKBXS UBR receipt chains."""

from __future__ import annotations

from collections import Counter, defaultdict, deque
from typing import Any

from . import schema


def receipt_id(receipt: dict[str, Any]) -> str:
    return str(receipt.get("id", ""))


def business_process_id(receipt: dict[str, Any]) -> str:
    return str(receipt.get("operation", {}).get("business_process_id", ""))


def parent_receipt_ids(receipt: dict[str, Any]) -> list[str]:
    return [str(item) for item in receipt.get("links", {}).get("parent_receipts", [])]


def validate_graph(
    receipts: list[dict[str, Any]],
    evidence_manifest: dict[str, Any] | None = None,
    verifier_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    ids = [receipt_id(receipt) for receipt in receipts if receipt_id(receipt)]
    duplicate_ids = sorted(rid for rid, count in Counter(ids).items() if count > 1)
    failures.extend(
        {"code": "duplicate_receipt_id", "receipt_id": rid, "message": f"Receipt id {rid} appears more than once."}
        for rid in duplicate_ids
    )
    by_id = {receipt_id(receipt): receipt for receipt in receipts if receipt_id(receipt)}

    for index, receipt in enumerate(receipts):
        try:
            schema.validate(receipt, "blkbxs.ubr.receipt.v1")
        except Exception as exc:  # pragma: no cover - exception detail is returned to callers
            failures.append({"code": "schema_invalid", "receipt_id": receipt_id(receipt) or str(index), "message": str(exc)})

    process_ids = {business_process_id(receipt) for receipt in receipts if business_process_id(receipt)}
    if len(process_ids) > 1:
        failures.append({"code": "mixed_business_process", "message": "UBR graph contains receipts from multiple business_process_id values."})

    children: dict[str, list[str]] = defaultdict(list)
    indegree = {rid: 0 for rid in by_id}
    for receipt in receipts:
        child_id = receipt_id(receipt)
        for parent_id in parent_receipt_ids(receipt):
            parent = by_id.get(parent_id)
            if parent is None:
                failures.append({"code": "missing_parent", "receipt_id": child_id, "message": f"Parent receipt {parent_id} is missing."})
                continue
            if business_process_id(parent) != business_process_id(receipt):
                failures.append({"code": "cross_process_parent", "receipt_id": child_id, "message": f"Parent receipt {parent_id} belongs to a different business process."})
                continue
            children[parent_id].append(child_id)
            indegree[child_id] = indegree.get(child_id, 0) + 1

    queue = deque(sorted([rid for rid, degree in indegree.items() if degree == 0]))
    order: list[str] = []
    while queue:
        current = queue.popleft()
        order.append(current)
        for child_id in sorted(children[current]):
            indegree[child_id] -= 1
            if indegree[child_id] == 0:
                queue.append(child_id)

    if len(order) != len(by_id):
        failures.append({"code": "cycle_detected", "message": "UBR graph contains a cycle."})

    evidence = evidence_summary(receipts, evidence_manifest)
    ai_boundary = ai_boundary_summary(receipts)
    if not ai_boundary["valid"]:
        failures.extend(ai_boundary["failures"])

    report_order = (verifier_report or {}).get("graph_results", {}).get("topological_order")
    if report_order and order and report_order != order:
        failures.append({"code": "verifier_report_order_mismatch", "message": "Verifier report topological order does not match the receipt graph."})

    return {
        "valid": not failures,
        "business_process_id": next(iter(process_ids), None),
        "receipt_count": len(receipts),
        "topological_order": order,
        "root_receipts": [rid for rid in order if not parent_receipt_ids(by_id[rid])],
        "terminal_receipts": [rid for rid in order if not children[rid]],
        "evidence_summary": evidence,
        "ai_boundary_summary": ai_boundary,
        "failures": failures,
    }


def evidence_summary(receipts: list[dict[str, Any]], evidence_manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest_items = list((evidence_manifest or {}).get("evidence", []))
    manifest_by_id = {item.get("id"): item for item in manifest_items}
    referenced = {item.get("id") for receipt in receipts for item in receipt.get("evidence", []) if item.get("id")}
    missing = sorted(evidence_id for evidence_id in referenced if evidence_id not in manifest_by_id)
    available = [item for item in manifest_items if item.get("available_to_verifier") is True]
    committed_only = [item for item in manifest_items if item.get("available_to_verifier") is False]
    return {
        "evidence_items": len(manifest_items),
        "referenced_evidence_items": len(referenced),
        "available_to_verifier": len(available),
        "committed_only": len(committed_only),
        "missing": missing,
        "sensitive_documents_committed_only": [item.get("id") for item in committed_only],
    }


def ai_boundary_summary(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    ai_receipts = [receipt for receipt in receipts if receipt.get("ai_assistance", {}).get("used") is True]
    final_decisions = [receipt for receipt in receipts if receipt.get("operation", {}).get("name") == "loan.application_decisioned"]
    human_review_receipts = {
        receipt_id(receipt)
        for receipt in receipts
        if receipt.get("operation", {}).get("name") == "human_credit_review.completed"
    }
    failures: list[dict[str, str]] = []

    for receipt in final_decisions:
        controls = receipt.get("ai_assistance", {}).get("risk_controls", {})
        systems = receipt.get("ai_assistance", {}).get("systems", [])
        human_required = bool(
            controls.get("human_review_receipt")
            or controls.get("human_approval_required_above_100k")
            or any(system.get("human_review_required") for system in systems)
        )
        human_completed = bool(
            controls.get("human_review_receipt") in human_review_receipts
            or any(system.get("human_review_completed") for system in systems)
        )
        if human_required and not human_completed:
            failures.append({
                "code": "human_review_missing",
                "receipt_id": receipt_id(receipt),
                "message": "Final loan decision requires completed human review evidence.",
            })

    return {
        "valid": not failures,
        "ai_used": bool(ai_receipts),
        "ai_receipt_count": len(ai_receipts),
        "final_decision_count": len(final_decisions),
        "human_review_receipt_count": len(human_review_receipts),
        "failures": failures,
    }


__all__ = [
    "ai_boundary_summary",
    "business_process_id",
    "evidence_summary",
    "parent_receipt_ids",
    "receipt_id",
    "validate_graph",
]
