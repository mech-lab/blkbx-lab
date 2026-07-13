from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from jsonschema import validate as validate_jsonschema

from internal.gates.policies import compile_policy, evaluate_gate
from internal.ink import _rust as rust_shim
from internal.ink.canonical import (
    canonical_json_hash,
    canonicalize,
    hash_bytes,
    hash_file,
    hash_text,
    sha256_bytes,
    strip_hash_prefix,
    tlv_field,
)


MANIFEST_SCHEMA = "ink.manifest.v2"
RECEIPT_SCHEMA = "ink.receipt.v2"
COMPARISON_SCHEMA = "receipt.comparison.v2"
MANIFEST_FILENAME = "ink_manifest.v2.json"
RECEIPT_FILENAME = "ink_receipt.v2.json"
TAMPERED_RECEIPT_FILENAME = "ink_receipt.tampered.v2.json"
COMPARISON_FILENAME = "receipt_comparison.v2.json"
CANONICALIZATION = "INK-CORE-TRANSCRIPT-V1"
SIGNING_ALGORITHM = "Ed25519"
DEV_KEY_ID = "dev-signature-v0.6"
DEMO_SIGNER_SEED = bytes.fromhex("0707070707070707070707070707070707070707070707070707070707070707")

MODEL_CLASS_CODE = {
    "open_weight": 0,
    "closed_weight": 1,
    "hosted_api": 2,
    "replay": 3,
    "deterministic_demo": 4,
}
RUNTIME_KIND_CODE = {
    "deterministic_demo": 0,
    "local_open_weight_model": 1,
    "local_closed_weight_model": 2,
    "hosted_model_api": 3,
    "hosted_model_gateway": 4,
    "external_process": 5,
    "replay_only": 6,
}
EXECUTION_TOPOLOGY_CODE = {
    "rule_based_local": 0,
    "local_process": 1,
    "local_container": 2,
    "remote_provider": 3,
    "remote_gateway": 4,
    "external_subprocess": 5,
    "replay_file": 6,
}
REPLAY_STRENGTH_CODE = {
    "fully_replayable": 0,
    "input_weights_config_bound": 1,
    "request_response_bound": 2,
    "declared_only": 3,
    "not_replayable": 4,
}
DATA_COLLECTION_CODE = {
    "declared_allow": 1,
    "declared_deny": 2,
    "unknown": 3,
}
FINISH_REASON_CODE = {
    "stop": 0,
    "length": 1,
    "tool_call": 2,
    "content_filter": 3,
    "error": 4,
    "unknown": 5,
}
PLUGIN_API_CODE = {"v1": 1}
RISK_CLASS_CODE = {"low": 0, "medium": 1, "high": 2}
PLUGIN_TRUST_CODE = {
    "untrusted": 0,
    "locally_allowed": 1,
    "first_party_reference": 2,
    "third_party_trusted": 3,
    "reproducibly_built": 4,
}
DECISION_CODE = {"pass": 1, "warn": 2, "escalate": 3, "block": 4}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _schema_path(filename: str) -> Path:
    return Path(__file__).with_name("schemas") / filename


def load_schema(filename: str) -> dict[str, Any]:
    return json.loads(_schema_path(filename).read_text(encoding="utf-8"))


def validate_payload(payload: dict[str, Any], schema_filename: str) -> None:
    validate_jsonschema(payload, load_schema(schema_filename))


def _digest_bytes(value: str | None) -> bytes:
    if value is None:
        return b""
    return bytes.fromhex(strip_hash_prefix(value))


def _hex_digest(raw: bytes) -> str:
    return f"sha256:{raw.hex()}"


def _safe_artifact_path(root: Path, relative_path: str) -> Path:
    path = (root / relative_path).resolve()
    if root.resolve() not in path.parents and path != root.resolve():
        raise ValueError(f"artifact path escapes manifest root: {relative_path}")
    return path


def artifact_index(manifest_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        artifact["artifact_type"]: artifact
        for artifact in manifest_data.get("artifacts", [])
        if isinstance(artifact, dict) and artifact.get("artifact_type")
    }


def build_artifact_descriptor(
    root: Path,
    relative_path: str,
    artifact_type: str,
    media_type: str,
    *,
    schema_hash: str | None = None,
) -> dict[str, Any]:
    target = root / relative_path
    rel = Path(relative_path).as_posix()
    return {
        "artifact_type": artifact_type,
        "media_type": media_type,
        "path": rel,
        "path_hash": hash_text(rel),
        "size_bytes": target.stat().st_size,
        "content_hash": hash_file(target),
        "schema_hash": schema_hash,
        "path_hint": rel,
    }


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_manifest(path: str | Path, payload: dict[str, Any]) -> None:
    validate_payload(payload, "ink_manifest.v2.schema.json")
    write_json(path, payload)


def load_manifest(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_payload(payload, "ink_manifest.v2.schema.json")
    return payload


def load_manifest_context(manifest_path: str | Path) -> dict[str, Any]:
    manifest = Path(manifest_path)
    manifest_data = load_manifest(manifest)
    if manifest_data.get("schema") != MANIFEST_SCHEMA:
        raise ValueError(f"{manifest} is not an {MANIFEST_SCHEMA} artifact")
    artifacts = artifact_index(manifest_data)
    action_artifact = artifacts.get("action_proposal")
    if action_artifact is None:
        raise ValueError(f"{manifest} is missing the action_proposal artifact entry")
    action_path = _safe_artifact_path(manifest.parent, action_artifact["path"])
    action = json.loads(action_path.read_text(encoding="utf-8"))
    prompt_text: str | None = None
    prompt_artifact = artifacts.get("prompt")
    if prompt_artifact is not None:
        prompt_path = _safe_artifact_path(manifest.parent, prompt_artifact["path"])
        if prompt_path.exists():
            prompt_text = prompt_path.read_text(encoding="utf-8")
    return {
        "manifest_path": manifest,
        "manifest": manifest_data,
        "artifacts": artifacts,
        "action": action,
        "action_id": manifest_data["action_id"],
        "prompt": prompt_text,
        "receipt_path": manifest.parent / RECEIPT_FILENAME,
    }


def _risk_class(action: dict[str, Any]) -> str:
    customer_impact = bool(action.get("customer_impact"))
    financial_consequence = bool(action.get("financial_consequence"))
    binding_effect = bool(action.get("binding_effect"))
    if customer_impact and financial_consequence:
        return "high"
    if customer_impact or financial_consequence or binding_effect:
        return "medium"
    return "low"


def normalize_model_claim(
    *,
    adapter_name: str,
    model_info: dict[str, Any],
    action: dict[str, Any],
    prompt: str | None,
) -> dict[str, Any]:
    model_ref_material = {
        "adapter": adapter_name,
        "model_id": model_info.get("model_id"),
        "provider": model_info.get("provider"),
        "runtime": "deterministic_demo",
        "version": "0.6.0",
    }
    plugin_material = {
        "adapter": adapter_name,
        "provider": model_info.get("provider"),
        "version": "0.6.0",
    }
    output_material = {"action": action, "adapter": adapter_name}
    return {
        "identity": {
            "model_class": "deterministic_demo",
            "model_ref_hash": canonical_json_hash(model_ref_material),
            "model_slug": adapter_name,
            "identity_evidence": {"kind": "declared"},
        },
        "invocation": {
            "action_hash": canonical_json_hash(action),
            "messages_hash": hash_text(prompt or ""),
            "system_prompt_hash": None,
            "tool_spec_hash": None,
            "response_schema_hash": None,
            "parameters_hash": canonical_json_hash({"adapter": adapter_name, "task": action.get("type")}),
            "requested_output": {"kind": "free_text"},
        },
        "observation": {
            "output_text_hash": canonical_json_hash(output_material),
            "structured_output_hash": None,
            "provider_metadata_hash": canonical_json_hash(model_info),
            "finish_reason": "stop",
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        },
        "runtime": {
            "runtime_kind": "deterministic_demo",
            "execution_topology": "rule_based_local",
            "replay_strength": "fully_replayable",
            "determinism": {"deterministic": True, "seed_bound": True},
            "isolation": {"process_isolated": True},
            "provider_routing": {
                "fallbacks_allowed": False,
                "provider_pinned": True,
                "data_collection_policy": "declared_deny",
            },
        },
        "plugin": {
            "plugin_id_hash": canonical_json_hash({"plugin": adapter_name}),
            "plugin_version_hash": canonical_json_hash({"plugin": adapter_name, "version": "0.6.0"}),
            "plugin_api_version": "v1",
            "maintainer_class": "first_party_reference",
            "normalization": {
                "input_normalized": True,
                "output_normalized": True,
                "raw_request_preserved": True,
                "raw_response_preserved": True,
                "secrets_redacted": True,
            },
            "plugin_manifest_hash": canonical_json_hash(plugin_material),
            "plugin_id_hint": adapter_name,
            "trust_level": "first_party_reference",
        },
    }


def build_policy_facts(action: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    risk_class = _risk_class(action)
    return {
        "risk_class": risk_class,
        "requires_human_review": risk_class == "high",
        "binding_effect_present": bool(action.get("binding_effect")),
        "provider_fallbacks_allowed": bool(model["runtime"]["provider_routing"]["fallbacks_allowed"]),
        "plugin_trust_level": model["plugin"]["trust_level"],
        "runtime_kind": model["runtime"]["runtime_kind"],
        "replay_strength": model["runtime"]["replay_strength"],
        "model_class": model["identity"]["model_class"],
    }


def normalize_controls(
    controls: list[dict[str, Any]] | None,
    *,
    action_hash: str,
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for item in controls or []:
        normalized.append(
            {
                "control_type": item["control_type"],
                "status": item.get("status", "approved"),
                "action_hash": action_hash,
                "actor_hash": hash_text(item.get("actor", "unknown")),
                "observed_at": item.get("observed_at", _iso_now()),
                "evidence_hash": item.get("evidence_hash") or canonical_json_hash(item),
            }
        )
    return normalized


def evaluate_policy(
    policy_name: str,
    *,
    action: dict[str, Any],
    model: dict[str, Any],
    controls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    facts = build_policy_facts(action, model)
    normalized_controls = normalize_controls(controls, action_hash=canonical_json_hash(action))
    result = evaluate_gate(policy_name, facts, controls=normalized_controls)
    return {
        "decision": result["decision"],
        "reasons": result["reasons"],
        "facts": facts,
        "controls": normalized_controls,
        "compiled_policy": result["compiled_policy"],
    }


def _u8(value: int) -> bytes:
    return bytes([value])


def _u32(value: int) -> bytes:
    return int(value).to_bytes(4, "big", signed=False)


def _i64(value: int) -> bytes:
    return int(value).to_bytes(8, "big", signed=True)


def _bool(value: bool) -> bytes:
    return _u8(1 if value else 0)


def _hash_runtime(runtime: dict[str, Any]) -> bytes:
    parts = [
        tlv_field(1, b"INK-RUNTIME-CLAIM-V1"),
        tlv_field(2, _u8(RUNTIME_KIND_CODE[runtime["runtime_kind"]])),
        tlv_field(3, _u8(EXECUTION_TOPOLOGY_CODE[runtime["execution_topology"]])),
        tlv_field(4, _u8(REPLAY_STRENGTH_CODE[runtime["replay_strength"]])),
        tlv_field(5, _bool(bool(runtime["determinism"]["deterministic"]))),
        tlv_field(6, _bool(bool(runtime["determinism"]["seed_bound"]))),
        tlv_field(7, _bool(bool(runtime["isolation"]["process_isolated"]))),
        tlv_field(8, _bool(bool(runtime["provider_routing"]["fallbacks_allowed"]))),
        tlv_field(9, _bool(bool(runtime["provider_routing"]["provider_pinned"]))),
        tlv_field(10, _u8(DATA_COLLECTION_CODE[runtime["provider_routing"]["data_collection_policy"]])),
    ]
    return sha256_bytes(b"".join(parts))


def _hash_plugin(plugin: dict[str, Any]) -> bytes:
    parts = [
        tlv_field(1, _digest_bytes(plugin["plugin_id_hash"])),
        tlv_field(2, _digest_bytes(plugin["plugin_version_hash"])),
        tlv_field(3, _u8(PLUGIN_API_CODE[plugin["plugin_api_version"]])),
        tlv_field(4, plugin["maintainer_class"].encode("utf-8")),
        tlv_field(5, _bool(bool(plugin["normalization"]["input_normalized"]))),
        tlv_field(6, _bool(bool(plugin["normalization"]["output_normalized"]))),
        tlv_field(7, _bool(bool(plugin["normalization"]["raw_request_preserved"]))),
        tlv_field(8, _bool(bool(plugin["normalization"]["raw_response_preserved"]))),
        tlv_field(9, _bool(bool(plugin["normalization"]["secrets_redacted"]))),
        tlv_field(10, _digest_bytes(plugin["plugin_manifest_hash"])),
        tlv_field(11, plugin["plugin_id_hint"].encode("utf-8")),
        tlv_field(12, _u8(PLUGIN_TRUST_CODE[plugin["trust_level"]])),
    ]
    return sha256_bytes(b"".join(parts))


def _hash_model(model: dict[str, Any]) -> bytes:
    identity = model["identity"]
    invocation = model["invocation"]
    observation = model["observation"]
    requested_output = invocation["requested_output"]
    evidence = identity["identity_evidence"]
    parts = [
        tlv_field(1, b"INK-MODEL-WAIST-V1"),
        tlv_field(2, _u8(MODEL_CLASS_CODE[identity["model_class"]])),
        tlv_field(3, _digest_bytes(identity["model_ref_hash"])),
        tlv_field(4, identity["model_slug"].encode("utf-8")),
    ]
    if evidence["kind"] == "declared":
        parts.append(tlv_field(5, _u8(1)))
    parts.extend(
        [
            tlv_field(9, _digest_bytes(invocation["action_hash"])),
            tlv_field(10, _digest_bytes(invocation["messages_hash"])),
            tlv_field(11, _digest_bytes(invocation.get("system_prompt_hash"))),
            tlv_field(12, _digest_bytes(invocation.get("tool_spec_hash"))),
            tlv_field(13, _digest_bytes(invocation.get("response_schema_hash"))),
            tlv_field(14, _digest_bytes(invocation["parameters_hash"])),
        ]
    )
    requested_kind = requested_output["kind"]
    requested_code = {"free_text": 1, "json_schema": 2, "tool_call": 3}[requested_kind]
    parts.append(tlv_field(15, _u8(requested_code)))
    if requested_kind == "json_schema":
        parts.append(tlv_field(16, _digest_bytes(requested_output["schema_hash"])))
    elif requested_kind == "tool_call":
        parts.append(tlv_field(16, _digest_bytes(requested_output["tool_spec_hash"])))
    parts.extend(
        [
            tlv_field(17, _digest_bytes(observation.get("output_text_hash"))),
            tlv_field(18, _digest_bytes(observation.get("structured_output_hash"))),
            tlv_field(19, _digest_bytes(observation.get("provider_metadata_hash"))),
            tlv_field(20, _u8(FINISH_REASON_CODE[observation["finish_reason"]])),
            tlv_field(21, _u32(observation["usage"].get("input_tokens") or 0)),
            tlv_field(22, _u32(observation["usage"].get("output_tokens") or 0)),
            tlv_field(23, _u32(observation["usage"].get("total_tokens") or 0)),
            tlv_field(24, _hash_runtime(model["runtime"])),
            tlv_field(25, _hash_plugin(model["plugin"])),
        ]
    )
    return sha256_bytes(b"".join(parts))


def _hash_facts(facts: dict[str, Any]) -> bytes:
    parts = [
        tlv_field(1, b"INK-POLICY-FACTS-V1"),
        tlv_field(2, _u8(RISK_CLASS_CODE[facts["risk_class"]])),
        tlv_field(3, _bool(bool(facts["requires_human_review"]))),
        tlv_field(4, _bool(bool(facts["binding_effect_present"]))),
        tlv_field(5, _bool(bool(facts["provider_fallbacks_allowed"]))),
        tlv_field(6, _u8(PLUGIN_TRUST_CODE[facts["plugin_trust_level"]])),
        tlv_field(7, _u8(RUNTIME_KIND_CODE[facts["runtime_kind"]])),
        tlv_field(8, _u8(REPLAY_STRENGTH_CODE[facts["replay_strength"]])),
        tlv_field(9, _u8(MODEL_CLASS_CODE[facts["model_class"]])),
    ]
    return sha256_bytes(b"".join(parts))


def receipt_transcript_bytes(receipt: dict[str, Any]) -> bytes:
    policy = receipt["policy"]
    issuer = receipt["issuer"]
    decision = receipt["decision"]
    evidence = receipt["evidence"]
    issued_at = datetime.fromisoformat(receipt["issued_at"].replace("Z", "+00:00"))
    seconds = int(issued_at.timestamp())
    parts = [
        tlv_field(1, CANONICALIZATION.encode("utf-8")),
        tlv_field(2, _u8(2)),
        tlv_field(3, receipt["receipt_id"].encode("utf-8")),
        tlv_field(4, _u8(1)),
        tlv_field(5, receipt["action_id"].encode("utf-8")),
        tlv_field(6, _i64(seconds)),
        tlv_field(7, _u32(issued_at.microsecond * 1000)),
        tlv_field(8, issuer["name"].encode("utf-8")),
        tlv_field(9, issuer["key_id"].encode("utf-8")),
        tlv_field(10, bytes.fromhex(issuer["public_key"])),
        tlv_field(11, _digest_bytes(receipt["manifest"]["manifest_hash"])),
        tlv_field(12, policy["policy_id"].encode("utf-8")),
        tlv_field(13, policy["policy_version"].encode("utf-8")),
        tlv_field(14, _digest_bytes(policy["policy_hash"])),
        tlv_field(15, _hash_runtime(receipt["model"]["runtime"])),
        tlv_field(16, _hash_model(receipt["model"])),
        tlv_field(17, _hash_facts(receipt["facts"])),
        tlv_field(18, _u8(DECISION_CODE[decision["decision"]])),
    ]
    for reason in decision["reasons"]:
        parts.append(tlv_field(19, reason.encode("utf-8")))
    parts.extend(
        [
            tlv_field(20, _digest_bytes(evidence["evidence_summary_hash"])),
            tlv_field(21, _digest_bytes(evidence["controls_summary_hash"])),
        ]
    )
    return b"".join(parts)


def receipt_payload_hash_bytes(receipt: dict[str, Any]) -> bytes:
    return sha256_bytes(receipt_transcript_bytes(receipt))


def receipt_payload_hash(receipt: dict[str, Any]) -> str:
    return _hex_digest(receipt_payload_hash_bytes(receipt))


def _public_key_from_seed(seed: bytes) -> bytes:
    if rust_shim.available():
        return rust_shim.public_key_from_seed(seed)
    return Ed25519PrivateKey.from_private_bytes(seed).public_key().public_bytes_raw()


def _sign_digest(digest: bytes, seed: bytes) -> bytes:
    if rust_shim.available():
        return rust_shim.sign_digest(digest, seed)
    return Ed25519PrivateKey.from_private_bytes(seed).sign(digest)


def _verify_digest(digest: bytes, public_key: bytes, signature: bytes) -> bool:
    if rust_shim.available():
        return rust_shim.verify_digest(digest, public_key, signature)
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, digest)
    except Exception:
        return False
    return True


def trusted_issuer_public_key_hex() -> str:
    return _public_key_from_seed(DEMO_SIGNER_SEED).hex()


def sign_receipt_payload(
    receipt: dict[str, Any],
    *,
    demo_signer: bool = False,
    signer_seed: bytes | None = None,
) -> dict[str, Any]:
    if signer_seed is None:
        if not demo_signer:
            raise ValueError("v0.6 requires explicit demo_signer=True or external signer material")
        signer_seed = DEMO_SIGNER_SEED
    digest = receipt_payload_hash_bytes(receipt)
    public_key = _public_key_from_seed(signer_seed)
    signature = _sign_digest(digest, signer_seed)
    signed = dict(receipt)
    signed["signing"] = {
        "canonicalization": CANONICALIZATION,
        "payload_hash": _hex_digest(digest),
        "algorithm": SIGNING_ALGORITHM,
        "key_id": signed["issuer"]["key_id"],
        "public_key": public_key.hex(),
        "signature": signature.hex(),
    }
    return signed


def verify_receipt_payload(receipt: dict[str, Any]) -> dict[str, Any]:
    validate_payload(receipt, "ink_receipt.v2.schema.json")
    signing = receipt.get("signing", {})
    expected_hash = receipt_payload_hash(receipt)
    if signing.get("payload_hash") != expected_hash:
        return {"valid": False, "reason": "payload_hash_mismatch", "payload_hash": expected_hash}
    if signing.get("algorithm") != SIGNING_ALGORITHM:
        return {"valid": False, "reason": "unsupported_algorithm", "payload_hash": expected_hash}
    key_id = signing.get("key_id")
    public_key_hex = signing.get("public_key", "")
    issuer_trusted = key_id == DEV_KEY_ID and public_key_hex == trusted_issuer_public_key_hex()
    valid_signature = _verify_digest(
        receipt_payload_hash_bytes(receipt),
        bytes.fromhex(public_key_hex),
        bytes.fromhex(signing.get("signature", "")),
    )
    if not valid_signature:
        return {
            "valid": False,
            "reason": "signature_mismatch",
            "payload_hash": expected_hash,
            "issuer_trusted": issuer_trusted,
        }
    return {
        "valid": True,
        "reason": "valid",
        "payload_hash": expected_hash,
        "issuer_trusted": issuer_trusted,
        "manifest_hash": receipt["manifest"]["manifest_hash"],
        "action_hash": receipt["model"]["invocation"]["action_hash"],
    }


def build_manifest_payload(
    *,
    action_id: str,
    created_at: str,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = {
        "schema": MANIFEST_SCHEMA,
        "action_id": action_id,
        "created_at": created_at,
        "artifacts": artifacts,
    }
    validate_payload(payload, "ink_manifest.v2.schema.json")
    return payload


def build_receipt_payload(
    *,
    action_id: str,
    receipt_id: str,
    issued_at: str,
    manifest_hash: str,
    policy_name: str,
    action: dict[str, Any],
    model: dict[str, Any],
    policy_eval: dict[str, Any],
) -> dict[str, Any]:
    compiled = policy_eval["compiled_policy"]
    controls = policy_eval["controls"]
    evidence_summary_hash = canonical_json_hash(
        {
            "action_hash": canonical_json_hash(action),
            "messages_hash": model["invocation"]["messages_hash"],
            "manifest_hash": manifest_hash,
        }
    )
    controls_summary_hash = canonical_json_hash(controls)
    payload = {
        "schema": RECEIPT_SCHEMA,
        "receipt_id": receipt_id,
        "receipt_profile": "thin_waist_v2",
        "action_id": action_id,
        "issued_at": issued_at,
        "issuer": {
            "name": "BLKBX Lab",
            "key_id": DEV_KEY_ID,
            "algorithm": SIGNING_ALGORITHM,
            "public_key": trusted_issuer_public_key_hex(),
        },
        "manifest": {"manifest_hash": manifest_hash},
        "policy": {
            "policy_id": compiled["policy_id"],
            "policy_version": compiled["policy_version"],
            "policy_hash": compiled["policy_hash"],
        },
        "model": model,
        "facts": policy_eval["facts"],
        "decision": {
            "decision": policy_eval["decision"],
            "reasons": list(policy_eval["reasons"]),
        },
        "evidence": {
            "manifest_hash": manifest_hash,
            "evidence_summary_hash": evidence_summary_hash,
            "controls_summary_hash": controls_summary_hash,
        },
        "controls": {"observations": controls},
    }
    return payload


def build_comparison_payload(left_receipt: dict[str, Any], right_receipt: dict[str, Any]) -> dict[str, Any]:
    left_verification = verify_receipt_payload(left_receipt)
    right_verification = verify_receipt_payload(right_receipt)
    if not left_verification.get("valid") or not right_verification.get("valid"):
        raise ValueError("compare requires both receipts to verify successfully")
    action_match = (
        left_receipt["model"]["invocation"]["action_hash"]
        == right_receipt["model"]["invocation"]["action_hash"]
    )
    if not action_match:
        raise ValueError("compare requires receipts for the same normalized action hash")
    payload = {
        "schema": COMPARISON_SCHEMA,
        "left_receipt_id": left_receipt["receipt_id"],
        "right_receipt_id": right_receipt["receipt_id"],
        "comparable": True,
        "decision_match": left_receipt["decision"]["decision"] == right_receipt["decision"]["decision"],
        "action_match": action_match,
        "manifest_match": left_receipt["manifest"]["manifest_hash"] == right_receipt["manifest"]["manifest_hash"],
    }
    validate_payload(payload, "receipt_comparison.v2.schema.json")
    return payload
