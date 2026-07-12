from typing import Any

def evaluate_action_gate(action: dict[str, Any]) -> dict[str, Any]:
    """Evaluate an action against the action-gate policy."""
    if action.get("customer_impact") and action.get("financial_consequence"):
        return {
            "decision": "block",
            "reason": "human_review_required"
        }
    if action.get("customer_impact") or action.get("financial_consequence"):
        return {
            "decision": "warn",
            "reason": "elevated_risk"
        }
    return {
        "decision": "pass",
        "reason": "low_risk"
    }

def evaluate_decision_gate(action: dict[str, Any]) -> dict[str, Any]:
    """Evaluate an action against the decision-gate policy."""
    if action.get("binding_effect"):
        return {
            "decision": "escalate",
            "reason": "binding_effect_requires_escalation"
        }
    return {
        "decision": "pass",
        "reason": "non_binding"
    }

def evaluate_trace_only(action: dict[str, Any]) -> dict[str, Any]:
    """Evaluate an action against the trace-only policy."""
    return {
        "decision": "pass",
        "reason": "trace_only"
    }

def evaluate_human_review_required(action: dict[str, Any]) -> dict[str, Any]:
    """Evaluate an action against the human-review-required policy."""
    return {
        "decision": "block",
        "reason": "human_review_required"
    }

POLICIES = {
    "action-gate": evaluate_action_gate,
    "decision-gate": evaluate_decision_gate,
    "trace-only": evaluate_trace_only,
    "human-review-required": evaluate_human_review_required,
}

def evaluate_gate(policy_name: str, action: dict[str, Any]) -> dict[str, Any]:
    policy_fn = POLICIES.get(policy_name)
    if not policy_fn:
        raise ValueError(f"Unknown policy: {policy_name}")
    return policy_fn(action)
