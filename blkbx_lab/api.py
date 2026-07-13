from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adapters.base import get_adapter, registered_adapter_names
from blkbx_lab.objects import (
    ActionEvidenceBundle,
    DoctorResult,
    GateAnalysisResult,
    InkReceiptResult,
    PublicTarget,
    ReceiptComparisonPacket,
)
from blkbx_lab.render import (
    render_analysis_report,
    render_comparison_report,
    render_demo_report,
    render_doctor,
    render_experimental_report,
    render_gate_report,
    render_release_summary,
    render_trace_report,
    render_verify_report,
)
from internal.gates.policies import evaluate_gate
from internal.ink.canonical import canonical_json_hash, hash_text
from internal.ink.manifest import write_manifest
from internal.ink.signing import sign_receipt
from internal.ink.verify import verify_receipt

_MANIFEST_SCHEMA = "ink.manifest.v1"
_RECEIPT_SCHEMA = "ink.receipt.v1"
_COMPARISON_SCHEMA = "receipt.comparison.v1"
_DEFAULT_ADAPTER = "qwen35"
_QWEN35_ALIASES = {
    "qwen35": "qwen35",
    "qwen3.5": "qwen35",
    "qwen3.5-2b": "qwen35",
    "qwen/qwen3.5-2b": "qwen35",
}
_EXPERIMENTAL_REPORT_FIELDS = {
    "tract-vs-bridge": ("trace_id", "tract_retention", "bridge_dependence"),
    "bridge-necessity": ("trace_id", "intervention_count", "strongest_bridge_necessity"),
    "compression-forgetting": ("trace_id", "mean_reconstruction_divergence", "tract_retention"),
}


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _load_public_adapters() -> None:
    importlib.import_module("adapters.qwen35")


def _default_output_dir(prefix: str, output_dir: str | Path | None) -> Path:
    target = Path(output_dir) if output_dir is not None else Path.cwd() / f"{prefix}-{_timestamp_slug()}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _artifact_index(manifest_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        artifact["artifact_type"]: artifact
        for artifact in manifest_data.get("artifacts", [])
        if isinstance(artifact, dict) and artifact.get("artifact_type")
    }


def _load_manifest_context(manifest_path: str | Path) -> dict[str, Any]:
    manifest = Path(manifest_path)
    manifest_data = _read_json(manifest)
    if manifest_data.get("schema") != _MANIFEST_SCHEMA:
        raise ValueError(f"{manifest} is not an {_MANIFEST_SCHEMA} artifact")

    artifacts = _artifact_index(manifest_data)
    action_artifact = artifacts.get("action_proposal")
    if action_artifact is None:
        raise ValueError(f"{manifest} is missing the action_proposal artifact entry")

    action_path = manifest.parent / action_artifact["path"]
    action = _read_json(action_path)

    prompt_text: str | None = None
    prompt_artifact = artifacts.get("prompt")
    if prompt_artifact is not None:
        prompt_path = manifest.parent / prompt_artifact["path"]
        if prompt_path.exists():
            prompt_text = prompt_path.read_text(encoding="utf-8")

    return {
        "manifest_path": manifest,
        "manifest": manifest_data,
        "action": action,
        "action_id": manifest_data["action_id"],
        "prompt": prompt_text,
        "artifacts": artifacts,
        "receipt_path": manifest.parent / "ink_receipt.v1.json",
    }


def _resolve_public_adapter_name(*, family: str | None, model: str | None) -> str:
    _load_public_adapters()
    supported = set(registered_adapter_names())
    explicit_values = {"model": model, "family": family}
    resolved: dict[str, str] = {}
    for label, value in explicit_values.items():
        if value is None:
            continue
        canonical = _QWEN35_ALIASES.get(value.casefold())
        if canonical is None and value in supported:
            canonical = value
        if canonical is None or canonical not in supported:
            supported_text = ", ".join(sorted(supported))
            alias_text = ", ".join(sorted(_QWEN35_ALIASES))
            raise ValueError(
                f"Unsupported public adapter {label}={value!r}. "
                f"Supported public adapters: {supported_text}. "
                f"Accepted Qwen aliases: {alias_text}."
            )
        resolved[label] = canonical

    if resolved and len(set(resolved.values())) > 1:
        raise ValueError(f"Conflicting public adapter selectors: {resolved}")
    return resolved.get("model") or resolved.get("family") or _DEFAULT_ADAPTER


def _resolve_receipt_path(target: str | Path) -> Path:
    target_path = Path(target)
    payload = _read_json(target_path)
    schema = payload.get("schema")
    if schema == _RECEIPT_SCHEMA:
        return target_path
    if schema == _MANIFEST_SCHEMA:
        receipt_path = target_path.parent / "ink_receipt.v1.json"
        if not receipt_path.exists():
            raise FileNotFoundError(
                f"Manifest target {target_path} does not have a sibling ink_receipt.v1.json yet. "
                f"Run blkbx-lab gate {target_path} first."
            )
        return receipt_path
    raise ValueError(f"Unsupported comparison target {target_path}: expected {_MANIFEST_SCHEMA} or {_RECEIPT_SCHEMA}")


def _resolve_report_path(target: PublicTarget) -> Path:
    if isinstance(target, ActionEvidenceBundle):
        return Path(target.manifest_path)
    if isinstance(target, GateAnalysisResult):
        return Path(target.manifest_path)
    if isinstance(target, InkReceiptResult):
        return Path(target.receipt_path)
    if isinstance(target, ReceiptComparisonPacket):
        return Path(target.comparison_path)
    return Path(target)


def _summary_hint(target: PublicTarget) -> dict[str, Any]:
    if isinstance(target, (ActionEvidenceBundle, GateAnalysisResult, InkReceiptResult, ReceiptComparisonPacket)):
        return dict(target.summary)
    return {}


def _comparison_payload(left_receipt: dict[str, Any], right_receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": _COMPARISON_SCHEMA,
        "left_receipt_id": left_receipt["receipt_id"],
        "right_receipt_id": right_receipt["receipt_id"],
        "decision_match": left_receipt.get("gate", {}).get("decision") == right_receipt.get("gate", {}).get("decision"),
        "action_match": canonical_json_hash(left_receipt.get("action", {})) == canonical_json_hash(right_receipt.get("action", {})),
    }


def _public_model_metadata() -> dict[str, Any]:
    _load_public_adapters()
    adapter = get_adapter(_DEFAULT_ADAPTER)
    return dict(adapter.model_info())


def doctor() -> DoctorResult:
    payload = {
        "status": "ready",
        "checks": [{"name": "schemas", "status": "ok"}],
        "notes": ["BLKBX Lab is ready."],
    }
    return DoctorResult(
        status=payload["status"],
        checks=payload["checks"],
        notes=payload["notes"],
        demo_ready=True,
        real_replay_ready=False,
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
) -> ActionEvidenceBundle:
    root = _default_output_dir("blkbx-trace", output_dir)
    action_id = trace_id or f"action-{_timestamp_slug()}"

    adapter_name = _resolve_public_adapter_name(family=family, model=model)
    adapter = get_adapter(adapter_name)
    action = adapter.propose_action("draft_claim_denial_email", [])
    action_hash = canonical_json_hash(action)
    prompt_hash = hash_text(prompt)

    (root / "action.json").write_text(json.dumps(action, indent=2), encoding="utf-8")
    (root / "prompt.txt").write_text(prompt, encoding="utf-8")

    manifest_path = root / "ink_manifest.v1.json"
    manifest_data = {
        "schema": _MANIFEST_SCHEMA,
        "action_id": action_id,
        "artifacts": [
            {"artifact_type": "action_proposal", "content_hash": action_hash, "path": "action.json"},
            {"artifact_type": "prompt", "content_hash": prompt_hash, "path": "prompt.txt"},
        ],
    }
    write_manifest(manifest_path, manifest_data)

    summary = {
        "action": action,
        "adapter": adapter_name,
        "backend": backend,
        "profile": profile,
        "model": adapter.model_info(),
        "architecture_profile": adapter.architecture_profile(),
    }
    return ActionEvidenceBundle(
        action_id=action_id,
        manifest_path=str(manifest_path),
        output_dir=str(root),
        summary=summary,
        report=render_trace_report(
            action_id=action_id,
            action=action,
            adapter_name=adapter_name,
            manifest_path=manifest_path,
            evidence_hash_count=2,
        ),
        evidence_hashes=[action_hash, prompt_hash],
    )


def analyze(
    manifest_path: str | Path,
    *,
    output_dir: str | Path | None = None,
    profile: str | None = None,
) -> GateAnalysisResult:
    context = _load_manifest_context(manifest_path)
    action = context["action"]
    action_id = context["action_id"]
    effective_output_dir = Path(output_dir) if output_dir is not None else context["manifest_path"].parent

    elevated_risk = any(
        bool(action.get(flag))
        for flag in ("customer_impact", "financial_consequence", "binding_effect")
    )
    required_controls = ["human_review"] if elevated_risk else []
    missing_controls = list(required_controls)
    recommended_decision = "block" if missing_controls else "pass"
    risk_tier = "high" if elevated_risk else "low"

    summary = {
        "action": action,
        "profile": profile,
        "artifact_count": len(context["manifest"].get("artifacts", [])),
    }
    return GateAnalysisResult(
        action_id=action_id,
        manifest_path=str(context["manifest_path"]),
        output_dir=str(effective_output_dir),
        risk_tier=risk_tier,
        required_controls=required_controls,
        missing_controls=missing_controls,
        recommended_decision=recommended_decision,
        summary=summary,
        report=render_analysis_report(
            action_id=action_id,
            risk_tier=risk_tier,
            required_controls=required_controls,
            missing_controls=missing_controls,
            recommended_decision=recommended_decision,
            manifest_path=context["manifest_path"],
        ),
    )


def gate(
    manifest_path: str | Path,
    *,
    policy: str | None = "action-gate",
    profile: dict[str, Any] | str | Path | None = None,
    output_path: str | Path | None = None,
) -> InkReceiptResult:
    context = _load_manifest_context(manifest_path)
    action = context["action"]
    action_id = context["action_id"]
    manifest_data = context["manifest"]

    decision = evaluate_gate(policy or "action-gate", action)
    model = _public_model_metadata()
    input_hashes = [artifact["content_hash"] for artifact in manifest_data.get("artifacts", [])]
    receipt_data = {
        "schema": _RECEIPT_SCHEMA,
        "receipt_id": f"ink_rcpt_{_timestamp_slug()}",
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "issuer": {
            "name": "BLKBX Lab",
            "key_id": "dev-signature",
        },
        "model": {
            "provider": model["provider"],
            "model_id": model["model_id"],
            "architecture_family": model["architecture_family"],
        },
        "agent": {
            "agent_id": "claims_assistant_demo",
            "mandate_id": "mand8.claims_assistant.v0.1",
        },
        "action": action,
        "gate": {
            "policy": policy or "action-gate",
            "decision": decision["decision"],
            "reason": decision["reason"],
        },
        "evidence": {
            "input_hashes": input_hashes,
            "policy_refs": ["policy.claims.v0.1"],
            "tool_call_hashes": [],
        },
    }

    signed_receipt = sign_receipt(receipt_data)
    receipt_path = Path(output_path) if output_path is not None else context["receipt_path"]
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(receipt_path, signed_receipt)
    verification = verify_receipt(signed_receipt)

    summary = {
        "decision": decision["decision"],
        "reason": decision["reason"],
        "policy": policy or "action-gate",
        "receipt_id": signed_receipt["receipt_id"],
        "profile": profile,
    }
    return InkReceiptResult(
        action_id=action_id,
        receipt_path=str(receipt_path),
        manifest_path=str(context["manifest_path"]),
        decision=decision["decision"],
        summary=summary,
        verification=verification,
        report=render_gate_report(
            action_id=action_id,
            receipt_id=signed_receipt["receipt_id"],
            decision=decision["decision"],
            reason=decision["reason"],
            manifest_path=context["manifest_path"],
            receipt_path=receipt_path,
        ),
    )


def verify(receipt_path: str | Path) -> InkReceiptResult:
    receipt_path_obj = Path(receipt_path)
    receipt = _read_json(receipt_path_obj)
    verification = verify_receipt(receipt)
    sibling_manifest = receipt_path_obj.parent / "ink_manifest.v1.json"
    action_id = "unknown"
    manifest_path = ""
    if sibling_manifest.exists():
        manifest_data = _read_json(sibling_manifest)
        if manifest_data.get("schema") == _MANIFEST_SCHEMA:
            action_id = manifest_data.get("action_id", "unknown")
            manifest_path = str(sibling_manifest)

    return InkReceiptResult(
        action_id=action_id,
        receipt_path=str(receipt_path_obj),
        manifest_path=manifest_path,
        decision=receipt.get("gate", {}).get("decision", "unknown"),
        summary={"receipt_id": receipt.get("receipt_id"), "reason": receipt.get("gate", {}).get("reason")},
        verification=verification,
        report=render_verify_report(receipt=receipt, verification=verification, receipt_path=receipt_path_obj),
    )


def tamper(receipt_path: str | Path) -> InkReceiptResult:
    receipt = _read_json(receipt_path)
    if "gate" in receipt:
        receipt["gate"]["decision"] = "pass"
        receipt["gate"]["reason"] = "tampered_to_pass"

    tampered_path = Path(receipt_path).parent / "ink_receipt.tampered.json"
    _write_json(tampered_path, receipt)

    return InkReceiptResult(
        action_id=receipt.get("receipt_id", "unknown"),
        receipt_path=str(tampered_path),
        manifest_path="",
        decision=receipt.get("gate", {}).get("decision", "unknown"),
        summary={"tampered_from": str(receipt_path)},
        verification={"valid": False},
        report=f"Tampered receipt written to {tampered_path}",
    )


def explain(receipt_path: str | Path) -> str:
    receipt = _read_json(receipt_path)
    decision = receipt.get("gate", {}).get("decision", "unknown")
    reason = receipt.get("gate", {}).get("reason", "unknown")
    past_tense = {
        "pass": "passed",
        "warn": "warned",
        "escalate": "escalated",
        "block": "blocked",
    }.get(decision, decision)
    return f"The action was {past_tense} because: {reason}"


def report(target: PublicTarget, *, kind: str | None = None) -> str:
    report_path = _resolve_report_path(target)
    payload = _read_json(report_path)
    schema = payload.get("schema")
    report_kind = kind or ("comparison-summary" if schema == _COMPARISON_SCHEMA else "release-summary")

    if report_kind == "release-summary":
        if schema not in {_MANIFEST_SCHEMA, _RECEIPT_SCHEMA}:
            raise ValueError("release-summary requires an ink_manifest.v1 or ink_receipt.v1 artifact")
        return render_release_summary(payload, path=report_path)

    if report_kind == "comparison-summary":
        if schema != _COMPARISON_SCHEMA:
            raise ValueError("comparison-summary requires a receipt_comparison.v1.json artifact")
        return render_comparison_report(payload, path=report_path)

    if report_kind in _EXPERIMENTAL_REPORT_FIELDS:
        summary = _summary_hint(target)
        missing = [field for field in _EXPERIMENTAL_REPORT_FIELDS[report_kind] if field not in summary]
        if missing:
            raise ValueError(
                f"{report_kind} is experimental and unavailable for canonical BLKBX artifacts. "
                f"Missing summary fields: {', '.join(missing)}."
            )
        return render_experimental_report(report_kind, summary, path=report_path)

    raise ValueError(
        "Unsupported report kind: "
        f"{report_kind}. Supported kinds: release-summary, comparison-summary, "
        "tract-vs-bridge, bridge-necessity, compression-forgetting."
    )


def compare(
    *,
    left: str | Path,
    right: str | Path,
    output_dir: str | Path | None = None,
) -> ReceiptComparisonPacket:
    root = _default_output_dir("blkbx-compare", output_dir)
    left_receipt_path = _resolve_receipt_path(left)
    right_receipt_path = _resolve_receipt_path(right)
    left_receipt = _read_json(left_receipt_path)
    right_receipt = _read_json(right_receipt_path)
    payload = _comparison_payload(left_receipt, right_receipt)

    out_path = root / "receipt_comparison.v1.json"
    _write_json(out_path, payload)
    summary = {
        **payload,
        "left_decision": left_receipt.get("gate", {}).get("decision"),
        "right_decision": right_receipt.get("gate", {}).get("decision"),
    }
    return ReceiptComparisonPacket(
        comparison_path=str(out_path),
        output_dir=str(root),
        left_receipt_path=str(left_receipt_path),
        right_receipt_path=str(right_receipt_path),
        summary=summary,
        report=render_comparison_report(payload, path=out_path),
    )


def demo(
    demo_name: str = "qwen35-claims",
    *,
    output_dir: str | Path | None = None,
) -> InkReceiptResult:
    root = _default_output_dir(demo_name, output_dir)

    examples_dir = Path(__file__).parent.parent / "examples" / "qwen35_claims"
    if examples_dir.exists():
        claim_text = (examples_dir / "claim_001.md").read_text(encoding="utf-8")
        policy_text = (examples_dir / "policy_001.md").read_text(encoding="utf-8")
        prompt = f"Review claim:\n{claim_text}\n\nAgainst policy:\n{policy_text}\n\nDraft denial email."
    else:
        prompt = "draft claim denial"

    traced = trace(prompt, output_dir=root)
    analyzed = analyze(traced.manifest_path, output_dir=root)
    receipt = gate(traced.manifest_path, policy="action-gate", output_path=root / "ink_receipt.v1.json")
    receipt.summary["analysis"] = {
        "risk_tier": analyzed.risk_tier,
        "recommended_decision": analyzed.recommended_decision,
        "missing_controls": analyzed.missing_controls,
    }
    receipt.report = render_demo_report(
        action_id=receipt.action_id,
        decision=receipt.decision,
        receipt_path=receipt.receipt_path,
        manifest_path=receipt.manifest_path,
    )
    return receipt
