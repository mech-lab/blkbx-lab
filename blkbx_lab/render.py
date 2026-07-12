from __future__ import annotations

import json
from pathlib import Path
from typing import Any


_REQUIRED_QWEN_HOOKS = (
    "pre-D1",
    "post-D1",
    "post-D2",
    "post-D3",
    "post-attention",
    "block-output",
)


def _fmt_path(path: str | Path | None) -> str:
    return str(path) if path is not None else "n/a"


def render_doctor(result: dict[str, Any]) -> str:
    lines = ["blkbx-lab doctor", f"Status: {result['status']}", ""]
    for check in result["checks"]:
        line = f"- {check['name']}: {check['status']}"
        if check.get("version"):
            line += f" ({check['version']})"
        lines.append(line)
        if check.get("message"):
            lines.append(f"  {check['message']}")
        if check.get("fix"):
            lines.append(f"  Fix: {check['fix']}")
    if result.get("notes"):
        lines.append("")
        lines.append("Notes:")
        for note in result["notes"]:
            lines.append(f"- {note}")
    return "\n".join(lines)


def render_receipt(receipt: dict[str, Any], *, receipt_path: str | Path | None = None) -> str:
    lines = [
        "BLKBX Lab Receipt",
        f"Trace: {receipt['trace_id']}",
        f"Decision: {receipt['decision']}",
        f"Receipt: {_fmt_path(receipt_path)}",
        "",
    ]
    passed = receipt.get("summary", {}).get("passed", [])
    failed = receipt.get("summary", {}).get("failed", [])
    notes = receipt.get("summary", {}).get("notes", [])
    if passed:
        lines.append("Passed gates:")
        for gate_name in passed:
            lines.append(f"- {gate_name}")
    if failed:
        lines.append("Failed gates:")
        for gate_name in failed:
            lines.append(f"- {gate_name}")
    if notes:
        lines.append("Notes:")
        for note in notes:
            lines.append(f"- {note}")
    return "\n".join(lines)


def render_bundle_summary(
    summary: dict[str, Any],
    *,
    manifest_path: str | Path | None = None,
    receipt_path: str | Path | None = None,
    title: str = "BLKBX Lab Evidence Bundle",
) -> str:
    hook_validation = summary.get("hook_validation", {})
    report_kinds = summary.get("report_kinds", [])
    lines = [
        title,
        f"Trace: {summary['trace_id']}",
        f"Manifest: {_fmt_path(manifest_path)}",
        f"Output dir: {_fmt_path(summary.get('output_dir'))}",
        f"Bundle digest: {summary.get('bundle_digest', 'n/a')}",
        f"Artifacts: {summary.get('artifact_count', 0)}",
        "",
        "Topology:",
        f"- backend: {summary.get('topology_backend', 'unknown')}",
        f"- bridge dependence: {summary.get('bridge_dependence', 'n/a')}",
        f"- tract retention: {summary.get('tract_retention', 'n/a')}",
        f"- gluing defect: {summary.get('gluing_defect', 'n/a')}",
    ]
    if summary.get("group_count") is not None:
        lines.extend(
            [
                "Grouped CLT:",
                f"- groups: {summary.get('group_count')}",
                f"- mean reconstruction divergence: {summary.get('mean_reconstruction_divergence', 'n/a')}",
                f"- mean bridge dependence: {summary.get('mean_group_bridge_dependence', 'n/a')}",
            ]
        )
    if hook_validation:
        lines.extend(
            [
                "Hook coverage:",
                f"- required: {', '.join(_REQUIRED_QWEN_HOOKS)}",
                f"- available: {', '.join(hook_validation.get('available', [])) or 'n/a'}",
                f"- missing: {', '.join(hook_validation.get('missing', [])) or 'none'}",
                f"- status: {'pass' if hook_validation.get('passed') else 'incomplete'}",
            ]
        )
    if summary.get("receipt_decision"):
        lines.extend(["Receipt:", f"- decision: {summary['receipt_decision']}", f"- path: {_fmt_path(receipt_path)}"])
    if report_kinds:
        lines.extend(["Report kinds:", *[f"- {kind}" for kind in report_kinds]])
    lines.extend(
        [
            "",
            "Next steps:",
            f"- blkbx-lab report {manifest_path}" if manifest_path else "- blkbx-lab report <manifest>",
            f"- blkbx-lab explain {receipt_path}" if receipt_path else "- blkbx-lab explain <receipt>",
            "- blkbx-lab doctor",
        ]
    )
    return "\n".join(lines)


def render_comparison(summary: dict[str, Any], *, comparison_path: str | Path | None = None) -> str:
    lines = [
        "BLKBX Lab Comparison Packet",
        f"Left trace: {summary['left_trace_id']}",
        f"Right trace: {summary['right_trace_id']}",
        f"Packet: {_fmt_path(comparison_path)}",
        f"Backend pair: {summary.get('backend_pair')}",
        f"Schema match: {summary.get('schema_match')}",
        f"Bridge delta: {summary.get('bridge_dependence_delta')}",
        f"Retention delta: {summary.get('tract_retention_delta')}",
        f"Topology distance: {summary.get('topology_distance')}",
    ]
    notes = summary.get("notes") or []
    if notes:
        lines.append("Notes:")
        for note in notes:
            lines.append(f"- {note}")
    return "\n".join(lines)


def render_report_kind(kind: str, summary: dict[str, Any], *, path: str | Path | None = None) -> str:
    kind = kind or "release-summary"
    if kind == "release-summary":
        return render_bundle_summary(summary, manifest_path=path, receipt_path=summary.get("receipt_path"), title="BLKBX Lab Release Summary")
    if kind == "tract-vs-bridge":
        lines = [
            "BLKBX Lab Report: tract-vs-bridge",
            f"Trace: {summary['trace_id']}",
            f"Manifest: {_fmt_path(path)}",
            f"Tract retention: {summary.get('tract_retention', 'n/a')}",
            f"Topology bridge dependence: {summary.get('bridge_dependence', 'n/a')}",
            f"Grouped bridge dependence: {summary.get('mean_group_bridge_dependence', 'n/a')}",
            f"Mean reconstruction divergence: {summary.get('mean_reconstruction_divergence', 'n/a')}",
        ]
        return "\n".join(lines)
    if kind == "bridge-necessity":
        strongest = summary.get("strongest_bridge_necessity") or {}
        lines = [
            "BLKBX Lab Report: bridge-necessity",
            f"Trace: {summary['trace_id']}",
            f"Manifest: {_fmt_path(path)}",
            f"Intervention rows: {summary.get('intervention_count', 0)}",
            f"Strongest group: {strongest.get('group_id', 'n/a')}",
            f"Strongest delta: {strongest.get('delta', 'n/a')}",
            f"Scaled strength: {strongest.get('strength', 'n/a')}",
        ]
        return "\n".join(lines)
    if kind == "compression-forgetting":
        lines = [
            "BLKBX Lab Report: compression-forgetting",
            f"Trace: {summary['trace_id']}",
            f"Manifest: {_fmt_path(path)}",
            f"Mean reconstruction divergence: {summary.get('mean_reconstruction_divergence', 'n/a')}",
            f"Retention after compression: {summary.get('tract_retention', 'n/a')}",
            f"Top group divergence: {summary.get('top_group_reconstruction_divergence', 'n/a')}",
        ]
        return "\n".join(lines)
    if kind == "comparison-summary":
        return render_comparison(summary, comparison_path=path)
    raise ValueError(f"Unsupported report kind: {kind}")


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)
