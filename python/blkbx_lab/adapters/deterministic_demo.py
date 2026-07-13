from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any


def _digest_bytes(data: bytes) -> dict[str, str]:
    return {"algorithm": "sha-256", "digest": hashlib.sha256(data).hexdigest()}


def _digest_text(text: str) -> dict[str, str]:
    return _digest_bytes(text.encode("utf-8"))


def _digest_json(payload: dict[str, Any]) -> dict[str, str]:
    return _digest_bytes(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    matched_rule_ids: tuple[str, ...]
    operation: str
    risk_class: str
    human_review_requested: bool
    response_kind: str = "json_schema"


def resolve_adapter(adapter: str | None) -> str:
    canonical = (adapter or "qwen35").casefold()
    if canonical in {"qwen35", "qwen35-claims", "qwen3.5", "qwen/qwen3.5-2b"}:
        return "qwen35"
    raise ValueError("Supported public adapters: qwen35")


def scenario_bundle(prompt: str, adapter: str) -> dict[str, Any]:
    prompt_lc = prompt.casefold()
    if _contains_any(prompt_lc, "high value", "large claim", "expensive") and _contains_any(
        prompt_lc, "without review", "skip reviewer", "auto approve"
    ):
        scenario = Scenario(
            scenario_id="high_value_without_review",
            matched_rule_ids=("amount.high", "review.absent"),
            operation="approve_claim",
            risk_class="high",
            human_review_requested=False,
        )
    elif _contains_any(prompt_lc, "override policy", "make exception", "supervisor override"):
        scenario = Scenario(
            scenario_id="policy_exception_request",
            matched_rule_ids=("policy.exception",),
            operation="request_policy_exception",
            risk_class="critical",
            human_review_requested=True,
        )
    else:
        scenario = Scenario(
            scenario_id="low_risk_status_update",
            matched_rule_ids=("default.low",),
            operation="draft_status_update",
            risk_class="low",
            human_review_requested=False,
        )

    prompt_hash = _digest_text(prompt)
    action = {
        "schema": "ink.action.v1",
        "operation": scenario.operation,
        "risk_class": scenario.risk_class,
        "human_review_requested": scenario.human_review_requested,
        "prompt_hash": prompt_hash,
        "scenario_id": scenario.scenario_id,
        "matched_rule_ids": list(scenario.matched_rule_ids),
    }
    runtime = {
        "schema": "ink.runtime.v1",
        "kind": "deterministic_demo",
        "adapter_id": adapter,
        "execution_topology": "rule_based_local",
        "replay_strength": "fully_replayable",
    }
    mapping = {
        "schema": "ink.demo-mapping.v1",
        "scenario_id": scenario.scenario_id,
        "matched_rule_ids": list(scenario.matched_rule_ids),
        "prompt_hash": prompt_hash,
    }
    parameters = {"adapter": adapter, "scenario_id": scenario.scenario_id}
    observation = {"decision_preview": scenario.operation, "risk_class": scenario.risk_class}
    model_waist = {
        "schema": "ink.model-waist.v1",
        "identity": {
            "model_class": "deterministic_demo",
            "model_ref_hash": _digest_text("blkbx-lab:qwen35:deterministic-demo"),
            "model_slug": "qwen35-demo",
            "identity_evidence": {"kind": "declared"},
        },
        "invocation": {
            "action_hash": _digest_json(action),
            "messages_hash": prompt_hash,
            "system_prompt_hash": None,
            "tool_spec_hash": None,
            "response_schema_hash": _digest_text("ink.action.v1"),
            "parameters_hash": _digest_json(parameters),
            "requested_output": {"kind": scenario.response_kind, "schema_hash": _digest_text("ink.action.v1")},
        },
        "observation": {
            "output_text_hash": None,
            "structured_output_hash": _digest_json(observation),
            "provider_metadata_hash": _digest_text(adapter),
            "finish_reason": "stop",
            "usage": {"input_tokens": None, "output_tokens": None, "total_tokens": None},
        },
        "runtime": {
            "runtime_kind": "deterministic_demo",
            "execution_topology": "rule_based_local",
            "replay_strength": "fully_replayable",
            "determinism": {
                "deterministic": True,
                "seed_bound": True,
            },
            "isolation": {
                "process_isolated": True,
            },
            "provider_routing": {
                "fallbacks_allowed": False,
                "provider_pinned": True,
                "data_collection_policy": "declared_deny",
            },
        },
        "plugin": {
            "plugin_id_hash": _digest_text(adapter),
            "plugin_version_hash": _digest_text("v1"),
            "plugin_api_version": "v1",
            "maintainer_class": "first_party_reference",
            "normalization": {
                "input_normalized": True,
                "output_normalized": True,
                "raw_request_preserved": True,
                "raw_response_preserved": True,
                "secrets_redacted": True,
            },
            "plugin_manifest_hash": _digest_text("blkbx-lab:deterministic-demo"),
            "plugin_id_hint": adapter,
            "trust_level": "first_party_reference",
        },
    }
    return {
        "scenario": scenario,
        "action": action,
        "runtime": runtime,
        "mapping": mapping,
        "model_waist": model_waist,
        "prompt_hash": prompt_hash["digest"],
    }


def _contains_any(prompt: str, *needles: str) -> bool:
    return any(needle in prompt for needle in needles)
