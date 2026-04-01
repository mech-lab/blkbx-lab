from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mech_lab._workspace import doctor_checks, ensure_workspace_imports, require_module
from mech_lab.objects import (
    AnalysisResult,
    ComparisonPacket,
    DoctorResult,
    EvidenceBundle,
    PublicArtifact,
    PublicTarget,
    ReceiptResult,
)
from mech_lab.render import (
    render_bundle_summary,
    render_comparison,
    render_doctor,
    render_receipt,
    render_report_kind,
)

_VERSION = "0.1.0"
_REQUIRED_QWEN_HOOKS = (
    "pre-D1",
    "post-D1",
    "post-D2",
    "post-D3",
    "post-attention",
    "block-output",
)
_QWEN_FAMILY_ALIASES = {"qwen3.5", "qwen35", "qwen3.5-hybrid", "qwen35-hybrid"}
_QWEN_MODEL_ALIASES = {
    "qwen3.5-2b": "qwen3.5-2b",
    "qwen/qwen3.5-2b": "qwen3.5-2b",
}
_BUILTIN_POLICIES: dict[str, dict[str, Any]] = {
    "release-assurance": {
        "required_artifacts": ["topology_summary", "grouped_clt_bundle", "offline_topology_report"],
        "max_bridge_dependence": 0.5,
        "max_gluing_defect": 1.5,
    },
    "incident-replay": {
        "required_artifacts": ["topology_summary", "grouped_clt_bundle", "offline_topology_report"],
        "max_bridge_dependence": 0.75,
        "max_gluing_defect": 2.0,
    },
}
_ANALYSIS_PROFILES = {
    "qwen3.5-hybrid": {"required_hooks": _REQUIRED_QWEN_HOOKS},
}
_HOOK_DISPLAY = {
    "pre_d1": "pre-D1",
    "post_d1": "post-D1",
    "post_d2": "post-D2",
    "post_d3": "post-D3",
    "post_attention": "post-attention",
    "block_output": "block-output",
}


def _timestamp_slug() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")


def _default_trace_id(prefix: str) -> str:
    return f"{prefix}-{_timestamp_slug()}"


def _default_output_dir(prefix: str, output_dir: str | Path | None) -> Path:
    target = Path(output_dir) if output_dir is not None else Path.cwd() / f"{prefix}-{_timestamp_slug()}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _normalize_family(raw: str | None) -> str | None:
    if raw is None:
        return None
    normalized = raw.strip().lower().replace("_", "-")
    return "qwen3.5" if normalized in _QWEN_FAMILY_ALIASES else normalized


def _normalize_model(raw: str | None) -> str | None:
    if raw is None:
        return None
    return _QWEN_MODEL_ALIASES.get(raw.strip().lower(), raw)


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_bundle(manifest_path: str | Path) -> dict[str, Any]:
    ensure_workspace_imports()
    mair_hydrate = require_module(
        "mair.hydrate",
        "Install MAIR editable or keep the workspace sibling repo available",
    )
    return mair_hydrate.load_artifact_bundle(manifest_path)


def _coerce_manifest_path(target: str | Path | EvidenceBundle | AnalysisResult | ReceiptResult) -> Path:
    if isinstance(target, (EvidenceBundle, AnalysisResult, ReceiptResult)):
        return Path(target.manifest_path)
    path = Path(target)
    if path.is_dir():
        candidate = path / "mair_manifest.v1.json"
        if candidate.exists():
            return candidate
    if path.name != "mair_manifest.v1.json":
        raise ValueError(f"Expected a MAIR manifest path, got: {path}")
    return path


def _coerce_receipt_path(target: str | Path | EvidenceBundle | AnalysisResult | ReceiptResult) -> Path:
    if isinstance(target, ReceiptResult):
        return Path(target.receipt_path)
    if isinstance(target, (EvidenceBundle, AnalysisResult)) and target.receipt_path is not None:
        return Path(target.receipt_path)
    path = Path(target)
    if path.is_dir():
        candidate = path / "assurance_receipt.v1.json"
        if candidate.exists():
            return candidate
    if path.name != "assurance_receipt.v1.json":
        raise ValueError(f"Expected an assurance receipt path, got: {path}")
    return path


def _coerce_comparison_path(target: str | Path | ComparisonPacket) -> Path:
    if isinstance(target, ComparisonPacket):
        return Path(target.comparison_path)
    path = Path(target)
    if path.is_dir():
        candidate = path / "backend_comparison.v1.json"
        if candidate.exists():
            return candidate
    if path.name != "backend_comparison.v1.json":
        raise ValueError(f"Expected a comparison packet path, got: {path}")
    return path


def _bundle_digest(manifest: dict[str, Any]) -> str:
    material = [manifest["trace_id"]]
    for artifact in sorted(manifest.get("artifacts", []), key=lambda item: item["artifact_type"]):
        material.append(f"{artifact['artifact_type']}:{artifact['content_hash']}")
    return hashlib.sha256("|".join(material).encode("utf-8")).hexdigest()[:16]


def _hook_validation(graph_ir: dict[str, Any], required_hooks: tuple[str, ...]) -> dict[str, Any]:
    present = sorted(
        {
            _HOOK_DISPLAY.get(str(node.get("kind", "")).lower(), str(node.get("kind", "")))
            for node in graph_ir.get("nodes", [])
            if isinstance(node, dict) and node.get("kind")
        }
    )
    missing = [hook for hook in required_hooks if hook not in present]
    return {
        "required": list(required_hooks),
        "available": present,
        "missing": missing,
        "passed": not missing,
    }


def _report_kinds_for_bundle(artifacts: dict[str, Any]) -> tuple[str, ...]:
    kinds = ["release-summary"]
    if "grouped_clt_bundle" in artifacts:
        kinds.extend(["compression-forgetting", "tract-vs-bridge"])
    if "intervention_sweep" in artifacts:
        kinds.append("bridge-necessity")
    if "backend_comparison" in artifacts:
        kinds.append("comparison-summary")
    return tuple(dict.fromkeys(kinds))


def _strongest_bridge_necessity(interventions: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not interventions:
        return None
    strongest = max(interventions, key=lambda row: abs(float(row.get("delta", 0.0))))
    return {
        "group_id": strongest.get("group_id"),
        "delta": strongest.get("delta"),
        "strength": (strongest.get("metadata") or {}).get("strength"),
    }


def _bundle_summary(bundle: dict[str, Any], manifest_path: str | Path, *, profile: str | None = None) -> dict[str, Any]:
    manifest = bundle["manifest"]
    artifacts = bundle["artifacts"]
    graph_ir = artifacts.get("mair_graph_ir", {})
    topology_summary = artifacts.get("topology_summary", {})
    grouped_bundle = artifacts.get("grouped_clt_bundle", {})
    interventions = artifacts.get("intervention_sweep", [])
    receipt = artifacts.get("assurance_receipt", {})
    groups = grouped_bundle.get("groups", [])
    hook_profile = profile or ("qwen3.5-hybrid" if _normalize_family(graph_ir.get("model_family")) == "qwen3.5" else None)
    required_hooks = tuple(_ANALYSIS_PROFILES.get(hook_profile, {}).get("required_hooks", ()))
    hook_validation = _hook_validation(graph_ir, required_hooks) if required_hooks else {}
    summary = {
        "trace_id": manifest["trace_id"],
        "output_dir": str(Path(manifest_path).parent),
        "artifact_count": len(manifest.get("artifacts", [])),
        "artifact_types": [artifact["artifact_type"] for artifact in manifest.get("artifacts", [])],
        "bundle_digest": _bundle_digest(manifest),
        "model_family": graph_ir.get("model_family"),
        "model_variant": graph_ir.get("model_variant"),
        "topology_backend": topology_summary.get("topology_backend", "unknown"),
        "bridge_dependence": topology_summary.get("bridge_dependence"),
        "tract_retention": topology_summary.get("tract_retention"),
        "gluing_defect": topology_summary.get("gluing_defect"),
        "group_count": grouped_bundle.get("summary_metrics", {}).get("group_count", len(groups)) if grouped_bundle else None,
        "mean_reconstruction_divergence": grouped_bundle.get("summary_metrics", {}).get("mean_reconstruction_divergence"),
        "mean_group_bridge_dependence": grouped_bundle.get("summary_metrics", {}).get("mean_bridge_dependence"),
        "top_group_reconstruction_divergence": max((group.get("reconstruction_divergence", 0.0) for group in groups), default=None),
        "intervention_count": len(interventions),
        "strongest_bridge_necessity": _strongest_bridge_necessity(interventions),
        "receipt_decision": receipt.get("decision"),
        "receipt_path": str(Path(manifest_path).parent / "assurance_receipt.v1.json") if receipt else None,
        "hook_validation": hook_validation,
        "analysis_profile": hook_profile,
        "report_kinds": list(_report_kinds_for_bundle(artifacts)),
    }
    return summary


def _build_bundle_object(manifest_path: str | Path) -> EvidenceBundle:
    bundle = _load_bundle(manifest_path)
    summary = _bundle_summary(bundle, manifest_path)
    return EvidenceBundle(
        trace_id=summary["trace_id"],
        manifest_path=str(manifest_path),
        output_dir=summary["output_dir"],
        summary=summary,
        report=render_bundle_summary(summary, manifest_path=manifest_path, receipt_path=summary.get("receipt_path")),
        bundle_digest=summary["bundle_digest"],
        receipt_path=summary.get("receipt_path"),
        report_kinds=tuple(summary["report_kinds"]),
    )


def _build_analysis_object(manifest_path: str | Path, *, profile: str | None = None) -> AnalysisResult:
    bundle = _load_bundle(manifest_path)
    summary = _bundle_summary(bundle, manifest_path, profile=profile)
    if profile in _ANALYSIS_PROFILES and summary["hook_validation"].get("missing"):
        missing = ", ".join(summary["hook_validation"]["missing"])
        raise ValueError(f"analysis profile {profile} is missing required hooks: {missing}")
    return AnalysisResult(
        trace_id=summary["trace_id"],
        manifest_path=str(manifest_path),
        output_dir=summary["output_dir"],
        summary=summary,
        report=render_bundle_summary(summary, manifest_path=manifest_path, receipt_path=summary.get("receipt_path"), title="mech-lab Analysis Result"),
        bundle_digest=summary["bundle_digest"],
        profile=profile or summary.get("analysis_profile"),
        receipt_path=summary.get("receipt_path"),
        report_kinds=tuple(summary["report_kinds"]),
    )


def _resolve_trace_runtime(
    *,
    backend: str | None,
    family: str | None,
    model: str | None,
    profile: str | Path | dict[str, Any] | None,
) -> tuple[str, str | Path | dict[str, Any] | None, str | None, str | None]:
    ensure_workspace_imports()
    blt_profiles = require_module("blt.profiles", "Install BLT editable or keep the workspace sibling repo available")

    normalized_family = _normalize_family(family)
    normalized_model = _normalize_model(model)
    selected_backend = backend or "mock"
    selected_profile = profile
    model_family = family
    model_variant = model

    if normalized_family == "qwen3.5" or normalized_model == "qwen3.5-2b":
        model_family = "qwen3.5-hybrid"
        model_variant = "Qwen/Qwen3.5-2B"
        if backend is None:
            selected_backend = "qwen_hybrid_hf"
        if selected_backend == "qwen_hybrid_hf" and selected_profile is None:
            selected_profile = str(blt_profiles.builtin_profile_path("qwen3.5-2b"))

    return selected_backend, selected_profile, model_family, model_variant


def _load_policy(policy: str | None, profile: dict[str, Any] | str | Path | None) -> dict[str, Any] | None:
    if isinstance(profile, (str, Path)):
        return json.loads(Path(profile).read_text(encoding="utf-8"))
    if isinstance(profile, dict):
        return profile
    if policy is None:
        return dict(_BUILTIN_POLICIES["release-assurance"])
    try:
        return dict(_BUILTIN_POLICIES[policy])
    except KeyError as exc:
        raise KeyError(f"unknown mech-lab policy: {policy}") from exc


def doctor() -> DoctorResult:
    checks = doctor_checks()
    ensure_workspace_imports()
    blt_profiles = require_module("blt.profiles", "Install BLT editable or keep the workspace sibling repo available")
    qwen_profile_path = blt_profiles.builtin_profile_path("qwen3.5-2b")
    checks.append(
        {
            "name": "qwen3.5_profile",
            "status": "ok" if qwen_profile_path.exists() else "missing",
            "message": str(qwen_profile_path) if qwen_profile_path.exists() else "builtin Qwen3.5 profile missing",
            "fix": None if qwen_profile_path.exists() else "Restore BLT configs/qwen3.5-2b.profile.json",
        }
    )
    demo_ready = all(check["status"] == "ok" for check in checks if check["name"] in {"hybrid_mechlab", "mair", "blt"})
    real_replay_ready = all(check["status"] == "ok" for check in checks if check["name"] in {"torch", "transformers", "qwen3.5_profile"})
    notes = [
        "mechlab demo is available when BLT and MAIR are importable.",
        "The mock backend is the product workflow gate; the Qwen runtime is the MVP real-model lane.",
    ]
    if real_replay_ready:
        notes.append("Qwen3.5-2B replay prerequisites are present; run `mechlab trace --family qwen3.5 --model qwen3.5-2b`." )
    payload = {
        "status": "ready" if demo_ready else "partial",
        "checks": checks,
        "notes": notes,
    }
    return DoctorResult(
        status=payload["status"],
        checks=checks,
        notes=notes,
        demo_ready=demo_ready,
        real_replay_ready=real_replay_ready,
        report=render_doctor(payload),
    )


def trace(
    prompt: str,
    *,
    output_dir: str | Path | None = None,
    trace_id: str | None = None,
    backend: str | None = None,
    family: str | None = None,
    model: str | None = None,
    profile: str | Path | dict[str, Any] | None = None,
    model_family: str | None = None,
    model_variant: str | None = None,
) -> EvidenceBundle:
    ensure_workspace_imports()
    blt_export = require_module("blt.export", "Install BLT editable or keep the workspace sibling repo available")
    root = _default_output_dir("mechlab-trace", output_dir)
    selected_trace_id = trace_id or _default_trace_id("trace-mechlab")
    selected_backend, selected_profile, resolved_family, resolved_model = _resolve_trace_runtime(
        backend=backend,
        family=family or model_family,
        model=model or model_variant,
        profile=profile,
    )
    manifest_path = blt_export.run_trace(
        prompt,
        selected_trace_id,
        root,
        backend=selected_backend,
        profile=selected_profile,
        model_family=resolved_family,
        model_variant=resolved_model,
        producer=f"mechlab:trace:{_VERSION}",
    )
    return _build_bundle_object(manifest_path)


def analyze(
    target: str | Path | EvidenceBundle | AnalysisResult,
    *,
    output_dir: str | Path | None = None,
    profile: str | None = None,
) -> AnalysisResult:
    ensure_workspace_imports()
    blt_export = require_module("blt.export", "Install BLT editable or keep the workspace sibling repo available")
    manifest_path = _coerce_manifest_path(target)
    analyzed_manifest_path = blt_export.run_analysis(manifest_path, output_dir=output_dir)
    return _build_analysis_object(analyzed_manifest_path, profile=profile)


def compare(
    *,
    left: str | Path | EvidenceBundle | AnalysisResult,
    right: str | Path | EvidenceBundle | AnalysisResult,
    output_dir: str | Path | None = None,
) -> ComparisonPacket:
    ensure_workspace_imports()
    mair_validate = require_module("mair.validate", "Install MAIR editable or keep the workspace sibling repo available")
    offline = require_module("hybrid_mechlab.topology.offline", "hybrid_mechlab is required for comparison packets")
    mair_integration = require_module("hybrid_mechlab.integrations.mair", "hybrid_mechlab MAIR integration is required")

    left_manifest = _coerce_manifest_path(left)
    right_manifest = _coerce_manifest_path(right)
    root = _default_output_dir("mechlab-compare", output_dir)
    left_trace = mair_integration.load_trace_from_mair_manifest(left_manifest)
    right_trace = mair_integration.load_trace_from_mair_manifest(right_manifest)
    comparison = offline.compare_persistence(left_trace, right_trace)
    summary = {
        "left_trace_id": comparison.left_trace_id,
        "right_trace_id": comparison.right_trace_id,
        "backend_pair": list(comparison.backend_pair),
        "schema_match": True,
        "bridge_dependence_delta": comparison.bridge_dependence_delta,
        "tract_retention_delta": comparison.tract_retention_delta,
        "topology_distance": abs(comparison.topology_drift_delta),
        "notes": [
            f"family_pair={comparison.family_pair[0]}->{comparison.family_pair[1]}",
            f"gluing_defect_delta={comparison.gluing_defect_delta}",
            f"left_manifest={left_manifest}",
            f"right_manifest={right_manifest}",
        ],
    }
    output_path = root / "backend_comparison.v1.json"
    output_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    mair_validate.validate_artifact(output_path, "backend_comparison")
    return ComparisonPacket(
        comparison_path=str(output_path),
        output_dir=str(root),
        left_manifest_path=str(left_manifest),
        right_manifest_path=str(right_manifest),
        summary=summary,
        report=render_comparison(summary, comparison_path=output_path),
    )


def gate(
    target: str | Path | EvidenceBundle | AnalysisResult,
    *,
    policy: str | None = "release-assurance",
    profile: dict[str, Any] | str | Path | None = None,
    output_path: str | Path | None = None,
) -> ReceiptResult:
    ensure_workspace_imports()
    mair_gates = require_module("mair.gates", "Install MAIR editable or keep the workspace sibling repo available")
    mair_manifest = require_module("mair.manifest", "Install MAIR editable or keep the workspace sibling repo available")

    manifest_path = _coerce_manifest_path(target)
    manifest_root = Path(manifest_path).parent
    if output_path is not None and Path(output_path).parent != manifest_root:
        raise ValueError("gate output_path must stay in the same run directory as the MAIR manifest")
    selected_profile = _load_policy(policy, profile)
    receipt_path = mair_gates.write_receipt(manifest_path, profile=selected_profile, output_path=output_path)
    manifest = mair_manifest.load_manifest(manifest_path)
    refreshed_manifest = mair_manifest.write_manifest(
        manifest_root,
        trace_id=manifest["trace_id"],
        producer=f"mechlab:gate:{_VERSION}",
    )
    receipt = _load_json(receipt_path)
    if isinstance(target, (EvidenceBundle, AnalysisResult)):
        target.receipt_path = str(receipt_path)
        target.summary["receipt_path"] = str(receipt_path)
        target.summary["receipt_decision"] = receipt["decision"]
        if "release-summary" not in target.report_kinds:
            target.report_kinds = tuple((*target.report_kinds, "release-summary"))
    return ReceiptResult(
        trace_id=receipt["trace_id"],
        receipt_path=str(receipt_path),
        manifest_path=str(refreshed_manifest),
        decision=receipt["decision"],
        summary=receipt.get("summary", {}),
        report=render_receipt(receipt, receipt_path=receipt_path),
    )


def explain(target: str | Path | EvidenceBundle | AnalysisResult | ReceiptResult) -> str:
    receipt_path = _coerce_receipt_path(target)
    receipt = _load_json(receipt_path)
    failed = receipt.get("summary", {}).get("failed", [])
    notes = receipt.get("summary", {}).get("notes", [])
    if not failed:
        return "\n".join(
            [
                f"Receipt {receipt_path} passed.",
                "The current evidence bundle satisfied the configured gates.",
                "Next step: share the bundle or compare it against another run if you need a procurement or rollout packet.",
            ]
        )

    mapping = {
        "has_topology_summary": "The bundle has no topology summary, so it cannot support a release decision. Run `mechlab analyze <manifest>`." ,
        "has_grouped_clt_bundle": "The bundle has no grouped CLT summary, so there is no concise concept-level view. Run `mechlab analyze <manifest>`." ,
        "has_offline_topology_report": "Exact topology artifacts are missing. Ensure hybrid-mechlab offline topology is available and rerun analysis.",
        "bridge_dependence_within_threshold": "Bridge dependence exceeded policy. The run relies too heavily on bridge steps relative to local tract steps.",
        "gluing_defect_within_threshold": "Gluing defect exceeded policy. Local sections do not stitch cleanly into a stable global explanation.",
    }
    lines = [f"Receipt {receipt_path} failed.", "Blocking findings:"]
    for gate_name in failed:
        lines.append(f"- {gate_name}: {mapping.get(gate_name, 'This gate failed; inspect the receipt and bundle report for details.')}")
    if notes:
        lines.append("Notes:")
        for note in notes:
            lines.append(f"- {note}")
    lines.append("Suggested next commands:")
    lines.append(f"- mechlab report {Path(receipt_path).parent / 'mair_manifest.v1.json'}")
    lines.append("- mechlab doctor")
    return "\n".join(lines)


def report(target: PublicTarget, *, kind: str | None = None) -> str:
    if isinstance(target, ComparisonPacket):
        return render_report_kind(kind or "comparison-summary", target.summary, path=target.comparison_path)
    if isinstance(target, ReceiptResult):
        return target.report if kind in {None, "receipt"} else render_receipt(_load_json(target.receipt_path), receipt_path=target.receipt_path)
    if isinstance(target, (EvidenceBundle, AnalysisResult)):
        default_kind = kind or ("release-summary" if target.receipt_path else target.report_kinds[0] if target.report_kinds else "release-summary")
        return render_report_kind(default_kind, {**target.summary, "receipt_path": target.receipt_path}, path=target.manifest_path)

    path = Path(target)
    if path.is_dir():
        if (path / "backend_comparison.v1.json").exists() and kind == "comparison-summary":
            path = path / "backend_comparison.v1.json"
        elif (path / "mair_manifest.v1.json").exists():
            path = path / "mair_manifest.v1.json"
        elif (path / "assurance_receipt.v1.json").exists():
            path = path / "assurance_receipt.v1.json"

    if path.name == "assurance_receipt.v1.json":
        return render_receipt(_load_json(path), receipt_path=path)
    if path.name == "backend_comparison.v1.json":
        return render_report_kind(kind or "comparison-summary", _load_json(path), path=path)
    if path.name != "mair_manifest.v1.json":
        raise ValueError(f"Unsupported report target: {path}")

    bundle = _load_bundle(path)
    summary = _bundle_summary(bundle, path)
    default_kind = kind or ("release-summary" if summary.get("receipt_path") else summary["report_kinds"][0] if summary["report_kinds"] else "release-summary")
    return render_report_kind(default_kind, summary, path=path)


def demo(
    *,
    output_dir: str | Path | None = None,
    trace_id: str | None = None,
    prompt: str = "Produce a deterministic mechanistic evidence bundle for a hybrid trace.",
) -> AnalysisResult:
    root = _default_output_dir("mechlab-demo", output_dir)
    selected_trace_id = trace_id or "trace-mechlab-demo"
    traced = trace(prompt, output_dir=root, trace_id=selected_trace_id, backend="mock")
    analyzed = analyze(traced, output_dir=root, profile="qwen3.5-hybrid")
    receipt = gate(analyzed, policy="release-assurance")
    return _build_analysis_object(receipt.manifest_path, profile=analyzed.profile)
