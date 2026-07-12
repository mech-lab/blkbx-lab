import pytest
from internal.gates.policies import evaluate_gate

def test_action_gate_pass():
    action = {
        "type": "draft_email",
        "customer_impact": False,
        "financial_consequence": False,
        "binding_effect": False
    }
    result = evaluate_gate("action-gate", action)
    assert result["decision"] == "pass"

def test_action_gate_warn():
    action = {
        "type": "draft_email",
        "customer_impact": True,
        "financial_consequence": False,
        "binding_effect": False
    }
    result = evaluate_gate("action-gate", action)
    assert result["decision"] == "warn"

def test_action_gate_block():
    action = {
        "type": "draft_email",
        "customer_impact": True,
        "financial_consequence": True,
        "binding_effect": False
    }
    result = evaluate_gate("action-gate", action)
    assert result["decision"] == "block"

def test_decision_gate_escalate():
    action = {
        "type": "send_email",
        "customer_impact": True,
        "financial_consequence": False,
        "binding_effect": True
    }
    result = evaluate_gate("decision-gate", action)
    assert result["decision"] == "escalate"
