"""Research-only actuarial annotations for already-issued receipts.

These helpers intentionally sit outside the receipt kernel. They interpret receipt
data for research reporting, but they do not define receipt validity or add signed
receipt fields.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from blkbx_lab._version import __version__

SCHEMA_ID = "ink.actuarial_annotation.v1"
STATUS = "research_unvalidated"
BADGE = "Research / unvalidated"
ENGINE_NAME = "blkbx_lab.research.actuarial"
DEFAULT_CASE_PROFILE = "mand8_case_v1"
GENERIC_RECEIPT_PROFILE = "generic_receipt_v1"

LIMITATIONS = [
    "Research/unvalidated annotation only.",
    "Does not alter or validate the receipt.",
    "Not a legal, actuarial, insurance, regulatory, reserve, capital, or safety determination.",
    "Evidence penalty is a research observability signal, not a reserve or capital formula.",
]

MAND8_CASE_WEIGHTS = {
    "identity": 0.12,
    "timestamp_sanity": 0.10,
    "integrity_verification": 0.18,
    "authority_mapping": 0.14,
    "human_review": 0.14,
    "event_trail": 0.10,
    "controls": 0.10,
    "incident_exception_transparency": 0.10,
    "domain_context": 0.12,
}

GENERIC_RECEIPT_WEIGHTS = {
    "identity": 0.20,
    "timestamp_sanity": 0.15,
    "integrity_verification": 0.25,
    "human_review": 0.15,
    "event_trail": 0.15,
    "domain_context": 0.10,
}

_PASSING_VERIFICATION_STATUSES = {"valid", "passed", "pass", "warning"}


def describe() -> dict[str, object]:
    return {
        "module": ENGINE_NAME,
        "schema": SCHEMA_ID,
        "status": STATUS,
        "badge": BADGE,
        "profiles": [DEFAULT_CASE_PROFILE, GENERIC_RECEIPT_PROFILE],
        "default_case_profile": DEFAULT_CASE_PROFILE,
        "annotation_integrity": "none",
        "limitations": list(LIMITATIONS),
    }


def annotate_receipt(
    receipt: dict[str, Any],
    *,
    profile: str = "auto",
    verification_reports: list[dict[str, Any]] | None = None,
    related_receipts: list[dict[str, Any]] | dict[str, Any] | None = None,
    computed_at: str | datetime | None = None,
) -> dict[str, Any]:
    base_receipt = copy.deepcopy(receipt)
    receipts = [base_receipt]
    receipts.extend(_normalize_related_receipts(related_receipts))
    resolved_profile = _resolve_profile(profile, receipts)
    return _annotate(receipts, profile=resolved_profile, verification_reports=verification_reports, computed_at=computed_at)


def annotate_case(
    receipts: list[dict[str, Any]],
    *,
    profile: str = DEFAULT_CASE_PROFILE,
    verification_reports: list[dict[str, Any]] | None = None,
    computed_at: str | datetime | None = None,
) -> dict[str, Any]:
    cloned = [copy.deepcopy(receipt) for receipt in receipts]
    resolved_profile = _resolve_profile(profile, cloned)
    return _annotate(cloned, profile=resolved_profile, verification_reports=verification_reports, computed_at=computed_at)


def _annotate(
    receipts: list[dict[str, Any]],
    *,
    profile: str,
    verification_reports: list[dict[str, Any]] | None,
    computed_at: str | datetime | None,
) -> dict[str, Any]:
    reports = [copy.deepcopy(report) for report in verification_reports or []]
    weights = MAND8_CASE_WEIGHTS if profile == DEFAULT_CASE_PROFILE else GENERIC_RECEIPT_WEIGHTS
    components, defects = _score_components(receipts, reports, profile=profile)
    completeness_score = _weighted_score(components, weights)
    defensibility_score = _defensibility_score(completeness_score, defects)
    evidence_penalty = round(1.0 + (1.0 - defensibility_score), 4)

    return {
        "schema": SCHEMA_ID,
        "status": STATUS,
        "badge": BADGE,
        "annotates": {
            "receipt_ids": _receipt_ids(receipts),
            "receipt_hashes": [_receipt_hash(receipt) for receipt in receipts],
            "case_id": _case_id(receipts),
        },
        "engine": {
            "name": ENGINE_NAME,
            "version": __version__,
            "profile": profile,
        },
        "computed_at": _computed_at(computed_at),
        "completeness_score": completeness_score,
        "defensibility_score": defensibility_score,
        "evidence_penalty": evidence_penalty,
        "components": components,
        "defects": defects,
        "limitations": list(LIMITATIONS),
    }


def _score_components(
    receipts: list[dict[str, Any]],
    reports: list[dict[str, Any]],
    *,
    profile: str,
) -> tuple[dict[str, float], list[dict[str, str]]]:
    defects: list[dict[str, str]] = []
    components: dict[str, float] = {
        "identity": _identity_score(receipts, defects),
        "timestamp_sanity": _timestamp_score(receipts, defects),
        "integrity_verification": _integrity_verification_score(receipts, reports, defects),
        "human_review": _human_review_score(receipts, defects),
        "event_trail": _event_trail_score(receipts, defects),
        "domain_context": _domain_context_score(receipts, defects, profile=profile),
    }
    if profile == DEFAULT_CASE_PROFILE:
        components.update(
            {
                "authority_mapping": _authority_mapping_score(receipts, defects),
                "controls": _controls_score(receipts, defects),
                "incident_exception_transparency": _incident_exception_score(receipts, defects),
            }
        )
    return components, defects


def _identity_score(receipts: list[dict[str, Any]], defects: list[dict[str, str]]) -> float:
    if not receipts:
        _add_defect(defects, "missing_receipt", "critical", "No receipt data was supplied.", "Paper 1")
        return 0.0
    present = 0
    total = len(receipts) * 3
    for receipt in receipts:
        present += 1 if receipt.get("schema") else 0
        present += 1 if receipt.get("receipt_id") else 0
        present += 1 if receipt.get("action_id") else 0
    score = present / total if total else 0.0
    if score < 1.0:
        _add_defect(defects, "missing_identity_coordinate", "major", "One or more receipts lack schema, receipt_id, or action_id.", "Paper 2")
    return score


def _timestamp_score(receipts: list[dict[str, Any]], defects: list[dict[str, str]]) -> float:
    if not receipts:
        return 0.0
    timestamps = [receipt.get("issued_at") for receipt in receipts]
    missing = [value for value in timestamps if not value]
    if missing:
        _add_defect(defects, "missing_timestamp", "major", "One or more receipts lack issued_at.", "Paper 2")
    invalid = [value for value in timestamps if value and _parse_time(value) is None]
    if invalid:
        _add_defect(defects, "invalid_timestamp", "major", "One or more receipts have an unparsable issued_at.", "Paper 2")
    valid_count = sum(1 for value in timestamps if value and _parse_time(value) is not None)
    return valid_count / len(receipts)


def _integrity_verification_score(
    receipts: list[dict[str, Any]],
    reports: list[dict[str, Any]],
    defects: list[dict[str, str]],
) -> float:
    if not receipts:
        return 0.0
    integrity_count = sum(1 for receipt in receipts if _receipt_integrity_digest(receipt))
    integrity_score = integrity_count / len(receipts)
    if integrity_score < 1.0:
        _add_defect(defects, "missing_integrity_digest", "major", "One or more receipts lack an integrity digest.", "Paper 3")

    if not reports:
        _add_defect(defects, "missing_verification_report", "moderate", "No external verification report was supplied to the annotation engine.", "Paper 3")
        verification_score = 0.0
    else:
        statuses = {_verification_status(report) for report in reports}
        verification_score = 1.0 if statuses & _PASSING_VERIFICATION_STATUSES else 0.0
        if verification_score == 0.0:
            _add_defect(defects, "failing_verification_report", "critical", "Verification reports did not include a passing status.", "Paper 3")
    return (integrity_score * 0.65) + (verification_score * 0.35)


def _authority_mapping_score(receipts: list[dict[str, Any]], defects: list[dict[str, str]]) -> float:
    statuses = []
    for receipt in receipts:
        status = receipt.get("authority_scope", {}).get("status") or receipt.get("domain_context", {}).get("authority_status")
        if status:
            statuses.append(str(status))
    if any(status == "within_authority" for status in statuses):
        return 1.0
    if statuses:
        _add_defect(defects, "non_conforming_authority_status", "major", "Authority evidence is present but is not within_authority.", "Paper 2")
        return 0.6
    _add_defect(defects, "missing_authority_mapping", "major", "No authority status was found for the case.", "Paper 2")
    return 0.0


def _human_review_score(receipts: list[dict[str, Any]], defects: list[dict[str, str]]) -> float:
    statuses = [receipt.get("human_review", {}).get("status") for receipt in receipts if isinstance(receipt.get("human_review"), dict)]
    if any(status == "reviewed" for status in statuses):
        return 1.0
    if any(status and status != "not_reviewed" for status in statuses):
        _add_defect(defects, "incomplete_human_review", "moderate", "Human review exists but is not marked reviewed.", "Paper 2")
        return 0.5
    _add_defect(defects, "absent_human_review", "major", "No reviewed human_review state was found.", "Paper 2")
    return 0.0


def _event_trail_score(receipts: list[dict[str, Any]], defects: list[dict[str, str]]) -> float:
    if not receipts:
        return 0.0
    non_empty = sum(1 for receipt in receipts if receipt.get("event_trail"))
    if non_empty < len(receipts):
        _add_defect(defects, "missing_event_trail", "major", "One or more receipts lack an event_trail.", "Paper 3")
    return non_empty / len(receipts)


def _controls_score(receipts: list[dict[str, Any]], defects: list[dict[str, str]]) -> float:
    has_control = any(_event_count(receipt, "control_check_recorded") > 0 for receipt in receipts)
    if has_control:
        return 1.0
    _add_defect(defects, "missing_control_evidence", "moderate", "No control_check_recorded event was found.", "Paper 5")
    return 0.0


def _incident_exception_score(receipts: list[dict[str, Any]], defects: list[dict[str, str]]) -> float:
    incident_receipts = [receipt for receipt in receipts if receipt.get("schema") == "mand8.incident_receipt.v1"]
    incident_events = sum(_event_count(receipt, "incident_recorded") for receipt in receipts)
    override_events = sum(_event_count(receipt, "override_recorded") for receipt in receipts)
    context_incident = any(receipt.get("domain_context", {}).get("last_incident_id") for receipt in receipts)
    if context_incident and not incident_receipts and incident_events == 0:
        _add_defect(defects, "unlinked_incident_context", "moderate", "Incident context exists without a linked incident receipt or event.", "Paper 2")
        return 0.5
    if override_events > 0 and not any(receipt.get("human_review", {}).get("status") == "reviewed" for receipt in receipts):
        _add_defect(defects, "unreviewed_override", "major", "Override evidence exists without reviewed human review.", "Paper 2")
        return 0.5
    return 1.0


def _domain_context_score(receipts: list[dict[str, Any]], defects: list[dict[str, str]], *, profile: str) -> float:
    if not receipts:
        return 0.0
    context = _merged_domain_context(receipts)
    if profile == DEFAULT_CASE_PROFILE:
        required = ("case_id", "policy_ref", "binder_ref", "risk_class", "exposure_unit_id")
    else:
        required = ("product_surface", "matter_id", "case_id")
    present = sum(1 for key in required if context.get(key) or _top_level_value(receipts, key))
    score = present / len(required)
    if score < 1.0:
        _add_defect(defects, "incomplete_domain_context", "moderate", "Domain context lacks one or more expected profile coordinates.", "Paper 1")
    return score


def _weighted_score(components: dict[str, float], weights: dict[str, float]) -> float:
    total = sum(weights.values())
    if total <= 0:
        return 0.0
    score = sum(_bounded(components.get(name, 0.0)) * weight for name, weight in weights.items()) / total
    return round(_bounded(score), 4)


def _defensibility_score(completeness_score: float, defects: list[dict[str, str]]) -> float:
    penalties = {"critical": 0.10, "major": 0.06, "moderate": 0.03, "minor": 0.01}
    penalty = sum(penalties.get(defect.get("severity", "minor"), 0.01) for defect in defects)
    return round(_bounded(completeness_score - penalty), 4)


def _bounded(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _normalize_related_receipts(related_receipts: list[dict[str, Any]] | dict[str, Any] | None) -> list[dict[str, Any]]:
    if related_receipts is None:
        return []
    if isinstance(related_receipts, dict):
        return [copy.deepcopy(related_receipts)]
    return [copy.deepcopy(receipt) for receipt in related_receipts]


def _resolve_profile(profile: str, receipts: list[dict[str, Any]]) -> str:
    if profile == "auto":
        return DEFAULT_CASE_PROFILE if any(str(receipt.get("schema", "")).startswith("mand8.") for receipt in receipts) else GENERIC_RECEIPT_PROFILE
    if profile not in {DEFAULT_CASE_PROFILE, GENERIC_RECEIPT_PROFILE}:
        raise ValueError(f"unsupported actuarial research profile {profile!r}")
    return profile


def _computed_at(value: str | datetime | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if isinstance(value, datetime):
        timestamp = value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return timestamp.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return value


def _receipt_ids(receipts: list[dict[str, Any]]) -> list[str]:
    return [str(receipt["receipt_id"]) for receipt in receipts if receipt.get("receipt_id")]


def _receipt_hash(receipt: dict[str, Any]) -> str:
    digest = _receipt_integrity_digest(receipt)
    if digest:
        return digest
    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _receipt_integrity_digest(receipt: dict[str, Any]) -> str | None:
    integrity = receipt.get("integrity")
    if not isinstance(integrity, dict):
        return None
    digest = integrity.get("digest")
    return str(digest) if digest else None


def _case_id(receipts: list[dict[str, Any]]) -> str | None:
    for receipt in receipts:
        case_id = receipt.get("case_id") or receipt.get("domain_context", {}).get("case_id")
        if case_id:
            return str(case_id)
    return None


def _merged_domain_context(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for receipt in receipts:
        context = receipt.get("domain_context")
        if isinstance(context, dict):
            merged.update({key: value for key, value in context.items() if value is not None})
    return merged


def _top_level_value(receipts: list[dict[str, Any]], key: str) -> Any:
    for receipt in receipts:
        value = receipt.get(key)
        if value is not None:
            return value
    return None


def _event_count(receipt: dict[str, Any], event_type: str) -> int:
    return sum(1 for entry in receipt.get("event_trail", []) if entry.get("event_type") == event_type)


def _verification_status(report: dict[str, Any]) -> str:
    return str(report.get("status") or report.get("summary_status") or report.get("overall") or "unknown").lower()


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _add_defect(defects: list[dict[str, str]], code: str, severity: str, message: str, source_paper: str) -> None:
    defects.append(
        {
            "code": code,
            "severity": severity,
            "message": message,
            "source_paper": source_paper,
        }
    )


__all__ = [
    "BADGE",
    "DEFAULT_CASE_PROFILE",
    "ENGINE_NAME",
    "GENERIC_RECEIPT_PROFILE",
    "LIMITATIONS",
    "SCHEMA_ID",
    "STATUS",
    "annotate_case",
    "annotate_receipt",
    "describe",
]
