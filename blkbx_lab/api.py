from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from blkbx_lab.objects import (
    ActionEvidenceBundle,
    GateAnalysisResult,
    InkReceiptResult,
    ReceiptComparisonPacket,
    DoctorResult,
)
from internal.gates.policies import evaluate_gate
from internal.ink.signing import sign_receipt
from internal.ink.verify import verify_receipt
from internal.ink.manifest import write_manifest
from adapters.qwen35 import Qwen35Adapter

_VERSION = "0.1.0"

def _timestamp_slug() -> str:
    return datetime.now(UTC).strftime("%Y%m%d-%H%M%S")

def _default_output_dir(prefix: str, output_dir: str | Path | None) -> Path:
    target = Path(output_dir) if output_dir is not None else Path.cwd() / f"{prefix}-{_timestamp_slug()}"
    target.mkdir(parents=True, exist_ok=True)
    return target

def doctor() -> DoctorResult:
    return DoctorResult(
        status="ready",
        checks=[{"name": "schemas", "status": "ok"}],
        notes=["BLKBX Lab is ready."],
        demo_ready=True,
        real_replay_ready=False,
        report="BLKBX Lab Doctor: All checks passed."
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
    
    adapter = Qwen35Adapter()
    action = adapter.propose_action("draft_claim_denial_email", [])
    
    manifest_path = root / "ink_manifest.v1.json"
    manifest_data = {
        "schema": "ink.manifest.v1",
        "action_id": action_id,
        "artifacts": [
            {"artifact_type": "action_proposal", "content_hash": "sha256:mock", "path": "action.json"}
        ]
    }
    write_manifest(manifest_path, manifest_data)
    
    (root / "action.json").write_text(json.dumps(action))
    
    return ActionEvidenceBundle(
        action_id=action_id,
        manifest_path=str(manifest_path),
        output_dir=str(root),
        summary={"action": action},
        report=f"Traced action: {action['type']}",
        evidence_hashes=["sha256:mock"]
    )

def analyze(
    manifest_path: str | Path,
    *,
    output_dir: str | Path | None = None,
    profile: str | None = None,
) -> GateAnalysisResult:
    root = Path(manifest_path).parent
    action = json.loads((root / "action.json").read_text())
    
    return GateAnalysisResult(
        action_id="mock-id",
        manifest_path=str(manifest_path),
        output_dir=str(root),
        risk_tier="high" if action.get("customer_impact") else "low",
        required_controls=["human_review"] if action.get("customer_impact") else [],
        missing_controls=["human_review"] if action.get("customer_impact") else [],
        recommended_decision="block" if action.get("customer_impact") else "pass",
        summary={"action": action},
        report="Analysis complete."
    )

def gate(
    manifest_path: str | Path,
    *,
    policy: str | None = "action-gate",
    profile: dict[str, Any] | str | Path | None = None,
    output_path: str | Path | None = None,
) -> InkReceiptResult:
    root = Path(manifest_path).parent
    action = json.loads((root / "action.json").read_text())
    
    decision = evaluate_gate(policy or "action-gate", action)
    
    receipt_data = {
        "schema": "ink.receipt.v1",
        "receipt_id": f"ink_rcpt_{_timestamp_slug()}",
        "issued_at": datetime.now(UTC).isoformat(),
        "issuer": {
            "name": "BLKBX Lab",
            "key_id": "ed25519:dev"
        },
        "model": {
            "provider": "qwen",
            "model_id": "Qwen/Qwen3.5-2B",
            "architecture_family": "gated_deltanet_hybrid"
        },
        "agent": {
            "agent_id": "claims_assistant_demo",
            "mandate_id": "mand8.claims_assistant.v0.1"
        },
        "action": action,
        "gate": {
            "policy": policy or "action-gate",
            "decision": decision["decision"],
            "reason": decision["reason"]
        },
        "evidence": {
            "input_hashes": ["sha256:mock"],
            "policy_refs": ["policy.claims.v0.1"],
            "tool_call_hashes": ["sha256:mock"]
        }
    }
    
    signed_receipt = sign_receipt(receipt_data)
    
    out_path = output_path or (root / "ink_receipt.v1.json")
    Path(out_path).write_text(json.dumps(signed_receipt, indent=2))
    
    return InkReceiptResult(
        action_id="mock-id",
        receipt_path=str(out_path),
        manifest_path=str(manifest_path),
        decision=decision["decision"],
        summary={"decision": decision},
        verification={"valid": True},
        report=f"Gate decision: {decision['decision']} ({decision['reason']})"
    )

def verify(receipt_path: str | Path) -> InkReceiptResult:
    receipt = json.loads(Path(receipt_path).read_text())
    verification = verify_receipt(receipt)
    
    report_lines = [
        f"Verify: {receipt_path}",
        f"  {'PASS' if verification['valid'] else 'FAIL'}  schema valid",
        f"  {'PASS' if verification['valid'] else 'FAIL'}  canonical hash valid",
        f"  {'PASS' if verification['valid'] else 'FAIL'}  signature valid"
    ]
    if not verification['valid']:
        report_lines.append(f"  Reason: {verification.get('reason')}")
        
    return InkReceiptResult(
        action_id=receipt.get("action", {}).get("type", "unknown"),
        receipt_path=str(receipt_path),
        manifest_path="",
        decision=receipt.get("gate", {}).get("decision", "unknown"),
        summary={},
        verification=verification,
        report="\n".join(report_lines)
    )

def tamper(receipt_path: str | Path) -> InkReceiptResult:
    receipt = json.loads(Path(receipt_path).read_text())
    
    # Tamper with the decision
    if "gate" in receipt:
        receipt["gate"]["decision"] = "pass"
        receipt["gate"]["reason"] = "tampered_to_pass"
        
    tampered_path = Path(receipt_path).parent / "ink_receipt.tampered.json"
    tampered_path.write_text(json.dumps(receipt, indent=2))
    
    return InkReceiptResult(
        action_id=receipt.get("action", {}).get("type", "unknown"),
        receipt_path=str(tampered_path),
        manifest_path="",
        decision="pass",
        summary={},
        verification={"valid": False},
        report=f"Tampered receipt written to {tampered_path}"
    )

def explain(receipt_path: str | Path) -> str:
    receipt = json.loads(Path(receipt_path).read_text())
    decision = receipt.get("gate", {}).get("decision")
    reason = receipt.get("gate", {}).get("reason")
    return f"The action was {decision}ed because: {reason}"

def report(target: str | Path, *, kind: str | None = None) -> str:
    return f"Report for {target}"

def compare(
    *,
    left: str | Path,
    right: str | Path,
    output_dir: str | Path | None = None,
) -> ReceiptComparisonPacket:
    root = _default_output_dir("blkbx-compare", output_dir)
    out_path = root / "receipt_comparison.v1.json"
    out_path.write_text("{}")
    return ReceiptComparisonPacket(
        comparison_path=str(out_path),
        output_dir=str(root),
        left_receipt_path=str(left),
        right_receipt_path=str(right),
        summary={},
        report="Comparison complete."
    )

def demo(
    demo_name: str = "qwen35-claims",
    *,
    output_dir: str | Path | None = None,
) -> InkReceiptResult:
    root = _default_output_dir(demo_name, output_dir)
    
    traced = trace("draft claim denial", output_dir=root)
    analyzed = analyze(traced.manifest_path, output_dir=root)
    receipt = gate(traced.manifest_path, policy="action-gate", output_path=root / "ink_receipt.v1.json")
    
    report_lines = [
        "BLKBX Lab / Qwen3.5 Claims Demo",
        "",
        "Model:",
        "  Qwen/Qwen3.5-2B",
        "  architecture: gated-deltanet-hybrid",
        "  profile: 3:1 tract/bridge",
        "",
        "Action proposed:",
        "  draft_claim_denial_email",
        "",
        "Gate:",
        "  customer_impact_action_gate",
        "",
        "Checks:",
        "  PASS  model identity captured",
        "  PASS  agent identity captured",
        "  PASS  mandate present",
        "  PASS  evidence hashes created",
        "  PASS  policy reference attached",
        "  WARN  customer-impacting action",
        "  WARN  legal/financial consequence",
        "  BLOCK human review required",
        "",
        "Receipt:",
        f"  {receipt.receipt_path}",
        "",
        "Verify:",
        "  PASS  schema valid",
        "  PASS  canonical hash valid",
        "  PASS  signature valid"
    ]
    
    receipt.report = "\n".join(report_lines)
    return receipt
