from __future__ import annotations

import importlib
import importlib.resources as resources
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters import resolve_adapter, scenario_bundle
from .compatibility import reject_decorative_options, resolve_public_adapter
from .results import (
    ActionEvidenceBundle,
    DoctorResult,
    GateAnalysisResult,
    InkReceiptResult,
    PublicTarget,
    ReceiptComparisonPacket,
)

_PACKAGE = __name__.rsplit(".", 1)[0]
_DEFAULT_POLICY = "demo-claims.v1.json"
_MANIFEST_FILENAME = "ink_manifest.v2.json"
_RECEIPT_FILENAME = "ink_receipt.v2.json"
_TAMPERED_RECEIPT_FILENAME = "ink_receipt.tampered.v2.json"
_COMPARISON_FILENAME = "receipt_comparison.v2.json"


def _native() -> Any:
    try:
        return importlib.import_module("blkbx_lab._ink_native")
    except Exception as exc:  # pragma: no cover - exact import failure depends on platform/build
        raise RuntimeError(
            "blkbx_lab._ink_native is unavailable. Build/install the native extension; "
            "there is no Python fallback for trust operations."
        ) from exc


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def _timestamp_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_output_dir(prefix: str, output_dir: str | Path | None) -> Path:
    root = Path(output_dir) if output_dir is not None else Path.cwd() / f"{prefix}-{_timestamp_slug()}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _resolve_receipt_path(target: str | Path) -> Path:
    path = Path(target)
    payload = _load_json(path)
    schema = payload.get("schema")
    if schema == "ink.receipt.v2":
        return path
    if schema == "ink.manifest.v2":
        receipt = path.parent / _RECEIPT_FILENAME
        if receipt.exists():
            return receipt
        raise FileNotFoundError(
            f"{receipt} does not exist. Run blkbx-lab gate --demo-signer or bl.gate(..., demo_signer=True) first."
        )
    raise ValueError(f"expected ink.manifest.v2 or ink.receipt.v2, got {schema!r}")


def _policy_path(policy: str | Path | None) -> Path:
    if policy is None:
        return Path(resources.files(f"{_PACKAGE}.policies").joinpath(_DEFAULT_POLICY))
    return Path(policy)


def _controls_payload(controls: str | Path | dict[str, Any] | list[dict[str, Any]] | None) -> str | None:
    if controls is None:
        return None
    payload: Any
    if isinstance(controls, dict):
        payload = controls
    elif isinstance(controls, list):
        payload = {"schema": "ink.controls.v1", "observations": controls}
    elif isinstance(controls, (str, Path)):
        path = Path(controls)
        text = path.read_text(encoding="utf-8") if path.exists() else str(controls)
        payload = json.loads(text)
    else:
        raise ValueError("controls must be a path, JSON text, dict, or list of dicts")

    if isinstance(payload, list):
        payload = {"schema": "ink.controls.v1", "observations": payload}
    elif isinstance(payload, dict) and payload.get("schema") != "ink.controls.v1":
        payload = {"schema": "ink.controls.v1", "observations": payload.get("observations", [payload])}

    return json.dumps(payload, sort_keys=True)


def _native_json(method: str, *args: Any) -> dict[str, Any]:
    result = getattr(_native(), method)(*args)
    if isinstance(result, bytes):
        result = result.decode("utf-8")
    if not isinstance(result, str):
        raise RuntimeError(f"native method {method} returned unsupported type {type(result)!r}")
    return json.loads(result)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _artifact_specs() -> list[dict[str, Any]]:
    return [
        {"artifact_type": "prompt_text", "path": "prompt.txt", "media_type": "text/plain; charset=utf-8"},
        {"artifact_type": "action_json", "path": "action.json", "media_type": "application/json", "schema_id": "ink.action.v1"},
        {"artifact_type": "runtime_json", "path": "runtime.json", "media_type": "application/json", "schema_id": "ink.runtime.v1"},
        {"artifact_type": "demo_mapping_json", "path": "demo_mapping.json", "media_type": "application/json", "schema_id": "ink.demo-mapping.v1"},
        {"artifact_type": "model_waist_json", "path": "model_waist.json", "media_type": "application/json", "schema_id": "ink.model-waist.v1"},
    ]


def doctor(*, initialize_local_issuer: bool = False) -> DoctorResult:
    payload = _native_json("doctor", initialize_local_issuer)
    return DoctorResult(
        status=payload["status"],
        checks=list(payload.get("checks", [])),
        notes=list(payload.get("notes", [])),
        demo_ready=bool(payload.get("demo_ready", True)),
        real_replay_ready=bool(payload.get("real_replay_ready", False)),
        report=payload.get("report", _doctor_report(payload)),
    )


def trace(
    prompt: str,
    *,
    output_dir: str | Path | None = None,
    trace_id: str | None = None,
    adapter: str | None = None,
    backend: str | None = None,
    family: str | None = None,
    model: str | None = None,
    profile: str | None = None,
) -> ActionEvidenceBundle:
    reject_decorative_options(backend=backend, family=family, model=model, profile=profile)
    root = _default_output_dir("blkbx-trace", output_dir)
    action_id = trace_id or f"urn:ink:action:{_timestamp_slug()}"
    adapter_name = resolve_adapter(resolve_public_adapter(adapter=adapter, family=family, model=model))
    bundle = scenario_bundle(prompt, adapter_name)

    (root / "prompt.txt").write_text(prompt, encoding="utf-8")
    _write_json(root / "action.json", bundle["action"])
    _write_json(root / "runtime.json", bundle["runtime"])
    _write_json(root / "demo_mapping.json", bundle["mapping"])
    _write_json(root / "model_waist.json", bundle["model_waist"])

    manifest = _native_json(
        "create_manifest",
        str(root),
        action_id,
        json.dumps(_artifact_specs(), sort_keys=True),
        _timestamp_iso(),
    )
    return ActionEvidenceBundle(
        action_id=manifest["action_id"],
        manifest_path=manifest["manifest_path"],
        output_dir=str(root),
        summary={
            "adapter": adapter_name,
            "scenario_id": bundle["scenario"].scenario_id,
            "runtime_kind": bundle["model_waist"]["runtime"]["runtime_kind"],
            "model_class": bundle["model_waist"]["identity"]["model_class"],
            "manifest_hash": manifest["manifest_hash"],
        },
        report="\n".join(
            [
                f"Trace captured for {manifest['action_id']}",
                f"Adapter: {adapter_name}",
                f"Scenario: {bundle['scenario'].scenario_id}",
                f"Manifest: {manifest['manifest_path']}",
            ]
        ),
        evidence_hashes=list(manifest.get("evidence_hashes", [])),
    )


def analyze(
    manifest_path: str | Path,
    *,
    policy: str | Path | None = None,
    controls: str | Path | dict[str, Any] | list[dict[str, Any]] | None = None,
    output_dir: str | Path | None = None,
    backend: str | None = None,
    family: str | None = None,
    model: str | None = None,
    profile: str | None = None,
) -> GateAnalysisResult:
    reject_decorative_options(backend=backend, family=family, model=model, profile=profile)
    payload = _native_json(
        "analyze",
        str(Path(manifest_path)),
        str(_policy_path(policy)),
        _controls_payload(controls),
    )
    return GateAnalysisResult(
        action_id=payload["action_id"],
        manifest_path=payload["manifest_path"],
        output_dir=str(output_dir or Path(payload["manifest_path"]).parent),
        risk_tier=payload["risk_tier"],
        required_controls=list(payload.get("required_controls", [])),
        missing_controls=list(payload.get("missing_controls", [])),
        recommended_decision=payload["recommended_decision"],
        summary=dict(payload.get("summary", {})),
        report=payload["report"],
    )


def gate(
    manifest_path: str | Path,
    *,
    policy: str | Path | None = None,
    controls: str | Path | dict[str, Any] | list[dict[str, Any]] | None = None,
    output_path: str | Path | None = None,
    backend: str | None = None,
    family: str | None = None,
    model: str | None = None,
    profile: str | None = None,
    demo_signer: bool = False,
) -> InkReceiptResult:
    reject_decorative_options(backend=backend, family=family, model=model, profile=profile)
    payload = _native_json(
        "gate",
        str(Path(manifest_path)),
        str(_policy_path(policy)),
        _controls_payload(controls),
        str(Path(output_path)) if output_path is not None else None,
        demo_signer,
    )
    return InkReceiptResult(
        action_id=payload["action_id"],
        receipt_path=payload["receipt_path"],
        manifest_path=payload.get("manifest_path"),
        decision=payload["decision"],
        summary=dict(payload.get("summary", {})),
        verification=dict(payload.get("verification", {})),
        report=payload["report"],
    )


def verify(receipt_path: str | Path, *, manifest_path: str | Path | None = None) -> InkReceiptResult:
    payload = _native_json(
        "verify",
        str(Path(receipt_path)),
        str(Path(manifest_path)) if manifest_path is not None else None,
    )
    verification = dict(payload.get("verification", {}))
    verification.setdefault("valid", verification.get("overall") == "pass")
    return InkReceiptResult(
        action_id=payload["action_id"],
        receipt_path=payload["receipt_path"],
        manifest_path=payload.get("manifest_path"),
        decision=payload["decision"],
        summary=dict(payload.get("summary", {})),
        verification=verification,
        report=payload["report"],
    )


def compare(
    left: str | Path,
    right: str | Path,
    *,
    output_dir: str | Path | None = None,
) -> ReceiptComparisonPacket:
    left_receipt = _resolve_receipt_path(left)
    right_receipt = _resolve_receipt_path(right)
    output_path = None
    if output_dir is not None:
        root = Path(output_dir)
        root.mkdir(parents=True, exist_ok=True)
        output_path = root / _COMPARISON_FILENAME
    payload = _native_json(
        "compare",
        str(left_receipt),
        str(right_receipt),
        str(output_path) if output_path is not None else None,
    )
    return ReceiptComparisonPacket(
        comparison_path=payload["comparison_path"],
        output_dir=payload["output_dir"],
        left_receipt_path=payload["left_receipt_path"],
        right_receipt_path=payload["right_receipt_path"],
        summary=dict(payload.get("summary", {})),
        report=payload["report"],
    )


def demo(
    demo_name: str = "qwen35",
    *,
    output_dir: str | Path | None = None,
) -> InkReceiptResult:
    doctor(initialize_local_issuer=True)
    prompt = "Draft a low-risk status update for a routine claim."
    bundle = trace(prompt, output_dir=output_dir, adapter=demo_name)
    result = gate(bundle.manifest_path, demo_signer=True)
    result.report = "\n".join(
        [
            "BLKBX Lab / qwen35 Demo",
            result.report,
        ]
    )
    return result


def tamper(receipt_path: str | Path) -> InkReceiptResult:
    source_path = Path(receipt_path)
    payload = _load_json(source_path)
    if payload.get("schema") == "ink.receipt.v2":
        payload["decision"] = "fail" if payload.get("decision") != "fail" else "pass"
        reason_codes = list(payload.get("reason_codes", []))
        if "TAMPERED_PAYLOAD" not in reason_codes:
            reason_codes.append("TAMPERED_PAYLOAD")
        payload["reason_codes"] = reason_codes
        output_path = source_path.with_name(_TAMPERED_RECEIPT_FILENAME)
    elif payload.get("schema") == "ink.receipt.v1":
        gate = dict(payload.get("gate", {}))
        gate["decision"] = "block" if gate.get("decision") != "block" else "allow"
        payload["gate"] = gate
        output_path = source_path.with_name("ink_receipt.tampered.json")
    else:
        raise ValueError(f"unsupported receipt schema in {source_path}")
    _write_json(output_path, payload)
    verified = verify(output_path)
    verified.report = "\n".join(
        [
            f"Tampered receipt at {output_path}",
            verified.report,
        ]
    )
    return verified


def explain(receipt_path: str | Path) -> str:
    payload = _load_json(receipt_path)
    schema = payload.get("schema", "unknown")
    if schema == "ink.receipt.v2":
        reasons = ", ".join(payload.get("reason_codes", [])) or "none"
        return "\n".join(
            [
                f"Receipt ID: {payload.get('receipt_id', 'unknown')}",
                f"Decision: {payload.get('decision', 'unknown')}",
                f"Reasons: {reasons}",
                f"Policy: {payload.get('policy', {}).get('id', 'unknown')}",
                f"Runtime kind: {payload.get('runtime', {}).get('runtime_kind', 'unknown')}",
            ]
        )
    if schema == "ink.receipt.v1":
        gate = payload.get("gate", {})
        return "\n".join(
            [
                f"Receipt ID: {payload.get('receipt_id', 'unknown')}",
                f"Decision: {gate.get('decision', 'unknown')}",
                "Legacy v1 receipts are integrity-only and not trusted v2 artifacts.",
            ]
        )
    raise ValueError(f"unsupported schema {schema}")


def report(target: PublicTarget, *, kind: str | None = None) -> str:
    path = _resolve_target_path(target)
    payload = _load_json(path)
    schema = payload.get("schema")
    if kind in {"tract-vs-bridge", "bridge-necessity", "compression-forgetting"}:
        raise ValueError("experimental and unavailable for canonical BLKBX artifacts")
    if kind is not None and kind not in {"release-summary", "comparison-summary"}:
        raise ValueError(f"unsupported report kind {kind}")
    if schema == "ink.manifest.v2":
        return "\n".join(
            [
                "BLKBX Lab Release Summary",
                f"Manifest: {path}",
                f"Action ID: {payload.get('action_id', 'unknown')}",
                f"Artifacts: {len(payload.get('artifacts', []))}",
            ]
        )
    if schema == "ink.receipt.v2":
        verification = verify(path)
        return "\n".join(["BLKBX Lab Release Summary", verification.report])
    if schema == "receipt.comparison.v2":
        return "\n".join(
            [
                "BLKBX Lab Comparison Summary",
                f"Comparison packet: {path}",
                f"Left receipt: {payload.get('left_receipt_id', 'unknown')}",
                f"Right receipt: {payload.get('right_receipt_id', 'unknown')}",
                f"Decision match: {payload.get('decision_match')}",
                f"Action match: {payload.get('action_match')}",
            ]
        )
    raise ValueError(f"unsupported report schema {schema}")


def _resolve_target_path(target: PublicTarget) -> Path:
    if isinstance(target, ActionEvidenceBundle):
        return Path(target.manifest_path)
    if isinstance(target, GateAnalysisResult):
        return Path(target.manifest_path)
    if isinstance(target, InkReceiptResult):
        return Path(target.receipt_path)
    if isinstance(target, ReceiptComparisonPacket):
        return Path(target.comparison_path)
    return Path(target)


def _doctor_report(payload: dict[str, Any]) -> str:
    lines = [f"BLKBX Lab Doctor\nStatus: {payload['status']}"]
    lines.extend(f"- {check['name']}: {check['status']}" for check in payload.get("checks", []))
    lines.extend(f"- {note}" for note in payload.get("notes", []))
    return "\n".join(lines)
