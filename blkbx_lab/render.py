from __future__ import annotations

from pathlib import Path
from typing import Any


def _fmt_path(path: str | Path | None) -> str:
    return str(path) if path is not None else "n/a"


def render_doctor(result: dict[str, Any]) -> str:
    lines = ["BLKBX Lab Doctor", f"Status: {result['status']}"]
    for check in result["checks"]:
        lines.append(f"- {check['name']}: {check['status']}")
    for note in result.get("notes", []):
        lines.append(f"- {note}")
    return "\n".join(lines)


def render_trace_report(
    *,
    action_id: str,
    action: dict[str, Any],
    adapter_name: str,
    manifest_path: str | Path,
    evidence_hash_count: int,
) -> str:
    return "\n".join(
        [
            f"Trace captured for {action_id}",
            f"Action: {action.get('type', 'unknown')}",
            f"Adapter: {adapter_name}",
            f"Evidence hashes: {evidence_hash_count}",
            f"Manifest: {_fmt_path(manifest_path)}",
        ]
    )


def render_analysis_report(
    *,
    action_id: str,
    risk_tier: str,
    required_controls: list[str],
    missing_controls: list[str],
    recommended_decision: str,
    manifest_path: str | Path,
) -> str:
    required = ", ".join(required_controls) if required_controls else "none"
    missing = ", ".join(missing_controls) if missing_controls else "none"
    return "\n".join(
        [
            f"Analysis for {action_id}",
            f"Risk tier: {risk_tier}",
            f"Recommended decision: {recommended_decision}",
            f"Required controls: {required}",
            f"Missing controls: {missing}",
            f"Manifest: {_fmt_path(manifest_path)}",
        ]
    )


def render_gate_report(
    *,
    action_id: str,
    receipt_id: str,
    decision: str,
    reason: str,
    manifest_path: str | Path,
    receipt_path: str | Path,
) -> str:
    return "\n".join(
        [
            f"Gate decision for {action_id}: {decision}",
            f"Reason: {reason}",
            f"Receipt ID: {receipt_id}",
            f"Manifest: {_fmt_path(manifest_path)}",
            f"Receipt: {_fmt_path(receipt_path)}",
        ]
    )


def render_verify_report(
    *,
    receipt: dict[str, Any],
    verification: dict[str, Any],
    receipt_path: str | Path,
) -> str:
    valid = verification.get("valid", False)
    lines = [
        f"Verification for {_fmt_path(receipt_path)}",
        f"Receipt ID: {receipt.get('receipt_id', 'unknown')}",
        f"Decision: {receipt.get('gate', {}).get('decision', 'unknown')}",
        f"Integrity: {'valid' if valid else 'invalid'}",
    ]
    if not valid and verification.get("reason"):
        lines.append(f"Reason: {verification['reason']}")
    return "\n".join(lines)


def render_demo_report(
    *,
    action_id: str,
    decision: str,
    receipt_path: str | Path,
    manifest_path: str | Path,
) -> str:
    return "\n".join(
        [
            "BLKBX Lab / Qwen3.5 Claims Demo",
            f"Action ID: {action_id}",
            f"Decision: {decision}",
            f"Manifest: {_fmt_path(manifest_path)}",
            f"Receipt: {_fmt_path(receipt_path)}",
        ]
    )


def render_release_summary(payload: dict[str, Any], *, path: str | Path | None = None) -> str:
    schema = payload.get("schema")
    lines = ["BLKBX Lab Release Summary"]
    if schema == "ink.manifest.v1":
        artifacts = payload.get("artifacts", [])
        lines.extend(
            [
                f"Action ID: {payload.get('action_id', 'unknown')}",
                f"Artifacts: {len(artifacts)}",
                f"Manifest: {_fmt_path(path)}",
            ]
        )
    elif schema == "ink.receipt.v1":
        lines.extend(
            [
                f"Receipt ID: {payload.get('receipt_id', 'unknown')}",
                f"Decision: {payload.get('gate', {}).get('decision', 'unknown')}",
                f"Policy: {payload.get('gate', {}).get('policy', 'unknown')}",
                f"Reason: {payload.get('gate', {}).get('reason', 'unknown')}",
                f"Action: {payload.get('action', {}).get('type', 'unknown')}",
                f"Receipt: {_fmt_path(path)}",
            ]
        )
    else:
        raise ValueError(f"Unsupported release-summary payload schema: {schema}")
    return "\n".join(lines)


def render_comparison_report(payload: dict[str, Any], *, path: str | Path | None = None) -> str:
    return "\n".join(
        [
            "BLKBX Lab Comparison Summary",
            f"Left receipt: {payload.get('left_receipt_id', 'unknown')}",
            f"Right receipt: {payload.get('right_receipt_id', 'unknown')}",
            f"Decision match: {payload.get('decision_match')}",
            f"Action match: {payload.get('action_match')}",
            f"Comparison packet: {_fmt_path(path)}",
        ]
    )


def render_experimental_report(kind: str, summary: dict[str, Any], *, path: str | Path | None = None) -> str:
    if kind == "tract-vs-bridge":
        return "\n".join(
            [
                "BLKBX Lab Report: tract-vs-bridge",
                f"Trace: {summary['trace_id']}",
                f"Manifest: {_fmt_path(path)}",
                f"Tract retention: {summary['tract_retention']}",
                f"Bridge dependence: {summary['bridge_dependence']}",
            ]
        )
    if kind == "bridge-necessity":
        strongest = summary["strongest_bridge_necessity"]
        return "\n".join(
            [
                "BLKBX Lab Report: bridge-necessity",
                f"Trace: {summary['trace_id']}",
                f"Manifest: {_fmt_path(path)}",
                f"Intervention rows: {summary['intervention_count']}",
                f"Strongest group: {strongest['group_id']}",
                f"Strongest delta: {strongest['delta']}",
            ]
        )
    if kind == "compression-forgetting":
        return "\n".join(
            [
                "BLKBX Lab Report: compression-forgetting",
                f"Trace: {summary['trace_id']}",
                f"Manifest: {_fmt_path(path)}",
                f"Mean reconstruction divergence: {summary['mean_reconstruction_divergence']}",
                f"Retention after compression: {summary['tract_retention']}",
            ]
        )
    raise ValueError(f"Unsupported report kind: {kind}")
