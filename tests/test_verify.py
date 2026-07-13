import pytest

from internal.ink.signing import sign_receipt
from internal.ink.verify import verify_receipt


@pytest.fixture
def clean_receipt() -> dict[str, object]:
    return {
        "schema": "ink.receipt.v1",
        "receipt_id": "ink_rcpt_test",
        "issued_at": "2026-07-12T00:00:00Z",
        "issuer": {"name": "BLKBX Lab", "key_id": "dev-signature"},
        "model": {"provider": "qwen", "model_id": "Qwen/Qwen3.5-2B", "architecture_family": "gated_deltanet_hybrid"},
        "agent": {"agent_id": "test_agent", "mandate_id": "test_mandate"},
        "action": {"type": "test_action", "customer_impact": False, "financial_consequence": False, "binding_effect": False},
        "gate": {"policy": "action-gate", "decision": "pass", "reason": "low_risk"},
        "evidence": {"input_hashes": ["sha256:test"], "policy_refs": ["policy.test"], "tool_call_hashes": []}
    }


def test_verify_clean(clean_receipt: dict[str, object]) -> None:
    signed = sign_receipt(clean_receipt)
    result = verify_receipt(signed)
    assert result["valid"] is True


def test_verify_tampered_decision(clean_receipt: dict[str, object]) -> None:
    signed = sign_receipt(clean_receipt)
    signed["gate"]["decision"] = "block"
    result = verify_receipt(signed)
    assert result["valid"] is False
    assert result["reason"] == "Hash mismatch"


def test_verify_tampered_action(clean_receipt: dict[str, object]) -> None:
    signed = sign_receipt(clean_receipt)
    signed["action"]["type"] = "malicious_action"
    result = verify_receipt(signed)
    assert result["valid"] is False
    assert result["reason"] == "Hash mismatch"


def test_verify_tampered_evidence(clean_receipt: dict[str, object]) -> None:
    signed = sign_receipt(clean_receipt)
    signed["evidence"]["input_hashes"] = ["sha256:malicious"]
    result = verify_receipt(signed)
    assert result["valid"] is False
    assert result["reason"] == "Hash mismatch"
