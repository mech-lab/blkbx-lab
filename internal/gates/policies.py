from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from internal.ink.canonical import canonical_json_hash


POLICY_DIR = Path(__file__).with_suffix("").with_name("policies")


def _risk_class_from_action(action: dict[str, Any]) -> str:
    customer_impact = bool(action.get("customer_impact"))
    financial_consequence = bool(action.get("financial_consequence"))
    binding_effect = bool(action.get("binding_effect"))
    if customer_impact and financial_consequence:
        return "high"
    if customer_impact or financial_consequence or binding_effect:
        return "medium"
    return "low"


def _facts_from_action(action: dict[str, Any]) -> dict[str, Any]:
    risk_class = _risk_class_from_action(action)
    return {
        "risk_class": risk_class,
        "requires_human_review": risk_class == "high",
        "binding_effect_present": bool(action.get("binding_effect")),
        "provider_fallbacks_allowed": False,
    }


def available_policy_names() -> tuple[str, ...]:
    return tuple(sorted(path.stem for path in POLICY_DIR.glob("*.json")))


def load_policy_spec(policy_name: str) -> dict[str, Any]:
    path = POLICY_DIR / f"{policy_name}.json"
    if not path.exists():
        raise ValueError(f"Unknown policy: {policy_name}")
    return json.loads(path.read_text(encoding="utf-8"))


def _compile_condition(condition: dict[str, Any], nodes: list[dict[str, Any]]) -> int:
    if "and" in condition:
        items = condition["and"]
        if len(items) < 2:
            raise ValueError("and conditions require at least two items")
        left = _compile_condition(items[0], nodes)
        for item in items[1:]:
            right = _compile_condition(item, nodes)
            nodes.append({"op": "and", "left": left, "right": right})
            left = len(nodes) - 1
        return left
    if "or" in condition:
        items = condition["or"]
        if len(items) < 2:
            raise ValueError("or conditions require at least two items")
        left = _compile_condition(items[0], nodes)
        for item in items[1:]:
            right = _compile_condition(item, nodes)
            nodes.append({"op": "or", "left": left, "right": right})
            left = len(nodes) - 1
        return left
    if "not" in condition:
        inner = _compile_condition(condition["not"], nodes)
        nodes.append({"op": "not", "left": inner})
        return len(nodes) - 1
    if "control" in condition:
        status = condition.get("status", "present").casefold()
        op = "control_approved" if status == "approved" else "control_present"
        nodes.append({"op": op, "value": condition["control"]})
        return len(nodes) - 1
    fact = condition["fact"]
    equals = condition.get("equals")
    op = {
        "risk_class": "risk_class_equals",
        "requires_human_review": "requires_human_review",
        "binding_effect_present": "binding_effect_present",
        "provider_fallbacks_allowed": "provider_fallbacks_allowed",
        "runtime_kind": "runtime_kind_equals",
        "replay_strength": "replay_strength_at_least",
        "model_class": "model_class_equals",
        "plugin_trust_level": "plugin_trust_level_equals",
    }[fact]
    node: dict[str, Any] = {"op": op}
    if equals is not None:
        node["value"] = equals
    nodes.append(node)
    return len(nodes) - 1


def compile_policy(policy_name: str) -> dict[str, Any]:
    spec = load_policy_spec(policy_name)
    nodes: list[dict[str, Any]] = []
    rules: list[dict[str, Any]] = []
    for rule in sorted(spec.get("rules", []), key=lambda item: item.get("priority", 0), reverse=True):
        root = _compile_condition(rule["when"], nodes) if "when" in rule else len(nodes)
        if "when" not in rule:
            nodes.append({"op": "always"})
        rules.append(
            {
                "id": rule["id"],
                "id_hash": canonical_json_hash({"id": rule["id"]}),
                "priority": rule.get("priority", 0),
                "root": root,
                "effect": dict(rule["effect"]),
            }
        )
    return {
        "schema": "ink.compiled_policy.v1",
        "policy_id": spec["id"],
        "policy_version": spec["version"],
        "policy_hash": canonical_json_hash(spec),
        "default_effect": dict(spec["default"]),
        "nodes": nodes,
        "rules": rules,
        "source": spec,
    }


def _control_present(controls: list[dict[str, Any]], control_type: str) -> bool:
    return any(item.get("control_type") == control_type for item in controls)


def _control_approved(controls: list[dict[str, Any]], control_type: str) -> bool:
    return any(
        item.get("control_type") == control_type
        and item.get("status") in {"present", "approved"}
        for item in controls
    )


def _eval_node(nodes: list[dict[str, Any]], idx: int, facts: dict[str, Any], controls: list[dict[str, Any]]) -> bool:
    node = nodes[idx]
    op = node["op"]
    if op == "always":
        return True
    if op == "risk_class_equals":
        return facts.get("risk_class") == node["value"]
    if op == "requires_human_review":
        expected = node.get("value", True)
        return bool(facts.get("requires_human_review")) is bool(expected)
    if op == "binding_effect_present":
        expected = node.get("value", True)
        return bool(facts.get("binding_effect_present")) is bool(expected)
    if op == "provider_fallbacks_allowed":
        expected = node.get("value", True)
        return bool(facts.get("provider_fallbacks_allowed")) is bool(expected)
    if op == "runtime_kind_equals":
        return facts.get("runtime_kind") == node["value"]
    if op == "replay_strength_at_least":
        order = {
            "fully_replayable": 0,
            "input_weights_config_bound": 1,
            "request_response_bound": 2,
            "declared_only": 3,
            "not_replayable": 4,
        }
        return order.get(facts.get("replay_strength"), 99) <= order.get(node["value"], 99)
    if op == "model_class_equals":
        return facts.get("model_class") == node["value"]
    if op == "plugin_trust_level_equals":
        return facts.get("plugin_trust_level") == node["value"]
    if op == "control_present":
        return _control_present(controls, node["value"])
    if op == "control_approved":
        return _control_approved(controls, node["value"])
    if op == "and":
        return _eval_node(nodes, node["left"], facts, controls) and _eval_node(nodes, node["right"], facts, controls)
    if op == "or":
        return _eval_node(nodes, node["left"], facts, controls) or _eval_node(nodes, node["right"], facts, controls)
    if op == "not":
        return not _eval_node(nodes, node["left"], facts, controls)
    raise ValueError(f"Unknown condition op: {op}")


def evaluate_gate(
    policy_name: str,
    payload: dict[str, Any],
    *,
    controls: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    facts = payload if "risk_class" in payload else _facts_from_action(payload)
    compiled = compile_policy(policy_name)
    controls = controls or []
    effect = dict(compiled["default_effect"])
    for rule in compiled["rules"]:
        if _eval_node(compiled["nodes"], rule["root"], facts, controls):
            effect = dict(rule["effect"])
            break
    return {
        "decision": effect["decision"],
        "reasons": [effect["reason"]],
        "compiled_policy": compiled,
        "facts": facts,
    }
