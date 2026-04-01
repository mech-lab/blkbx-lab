from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .hydrate import load_artifact_bundle
from .validate import validate_artifact


DEFAULT_GATE_PROFILE: dict[str, Any] = {
    "required_artifacts": ["topology_summary", "grouped_clt_bundle"],
    "max_bridge_dependence": 1.0,
    "max_gluing_defect": 1.0,
}


def _merge_profile(profile: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(DEFAULT_GATE_PROFILE)
    if profile:
        merged.update(profile)
    merged["required_artifacts"] = list(merged.get("required_artifacts", []))
    return merged


def _artifact_inputs(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_type": artifact["artifact_type"],
            "artifact_id": artifact["artifact_id"],
            "content_hash": artifact["content_hash"],
        }
        for artifact in manifest.get("artifacts", [])
    ]


def _bridge_dependence(artifacts: dict[str, Any]) -> float | None:
    topology_summary = artifacts.get("topology_summary", {})
    offline_report = artifacts.get("offline_topology_report", {})
    value = topology_summary.get("bridge_dependence")
    if value is None:
        value = (offline_report.get("summary") or {}).get("bridge_dependence")
    return None if value is None else float(value)


def _gluing_defect(artifacts: dict[str, Any]) -> float | None:
    topology_summary = artifacts.get("topology_summary", {})
    offline_report = artifacts.get("offline_topology_report", {})
    value = topology_summary.get("gluing_defect")
    if value is None:
        value = (offline_report.get("summary") or {}).get("gluing_defect")
    return None if value is None else float(value)


def run_gates(manifest_path: str | Path, profile: dict[str, Any] | None = None) -> dict[str, Any]:
    gate_profile = _merge_profile(profile)
    bundle = load_artifact_bundle(manifest_path)
    manifest = bundle["manifest"]
    artifacts = bundle["artifacts"]
    gates: dict[str, bool] = {}
    notes: list[str] = []

    gates["manifest_valid"] = True
    for artifact_type in gate_profile["required_artifacts"]:
        gate_name = f"has_{artifact_type}"
        gates[gate_name] = artifact_type in artifacts
        if not gates[gate_name]:
            notes.append(f"missing required artifact: {artifact_type}")

    gates["has_topology_summary"] = "topology_summary" in artifacts
    if not gates["has_topology_summary"]:
        notes.append("topology summary is required for gating")

    gates["has_grouped_clt_bundle"] = "grouped_clt_bundle" in artifacts
    if not gates["has_grouped_clt_bundle"]:
        notes.append("grouped CLT bundle is required for gating")

    bridge_dependence = _bridge_dependence(artifacts)
    max_bridge_dependence = gate_profile.get("max_bridge_dependence")
    gates["bridge_dependence_within_threshold"] = (
        bridge_dependence is not None and max_bridge_dependence is not None and bridge_dependence <= float(max_bridge_dependence)
    )
    if bridge_dependence is None:
        notes.append("bridge dependence metric unavailable")

    gluing_defect = _gluing_defect(artifacts)
    max_gluing_defect = gate_profile.get("max_gluing_defect")
    gates["gluing_defect_within_threshold"] = (
        gluing_defect is not None and max_gluing_defect is not None and gluing_defect <= float(max_gluing_defect)
    )
    if gluing_defect is None:
        notes.append("gluing defect metric unavailable")

    passed = [gate for gate, decision in gates.items() if decision]
    failed = [gate for gate, decision in gates.items() if not decision]
    falsifiers = {
        "bridge_dependence_exceeded": bool(
            bridge_dependence is not None
            and max_bridge_dependence is not None
            and bridge_dependence > float(max_bridge_dependence)
        ),
        "gluing_defect_exceeded": bool(
            gluing_defect is not None
            and max_gluing_defect is not None
            and gluing_defect > float(max_gluing_defect)
        ),
    }
    decision = "pass" if not failed else "fail"
    return {
        "trace_id": manifest["trace_id"],
        "decision": decision,
        "gates": gates,
        "falsifiers": falsifiers,
        "artifact_inputs": _artifact_inputs(manifest),
        "summary": {
            "passed": passed,
            "failed": failed,
            "notes": notes,
        },
    }


def write_receipt(
    manifest_path: str | Path,
    *,
    profile: dict[str, Any] | None = None,
    output_path: str | Path | None = None,
) -> Path:
    receipt = run_gates(manifest_path, profile=profile)
    target = (
        Path(output_path)
        if output_path is not None
        else Path(manifest_path).parent / "assurance_receipt.v1.json"
    )
    target.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    validate_artifact(target, "assurance_receipt")
    return target
