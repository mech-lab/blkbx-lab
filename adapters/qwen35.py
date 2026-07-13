from __future__ import annotations

from typing import Any

from .base import register_adapter


class Qwen35Adapter:
    def model_info(self) -> dict[str, Any]:
        return {
            "model_id": "Qwen/Qwen3.5-2B",
            "provider": "qwen",
            "runtime": "transformers",
            "architecture_family": "gated_deltanet_hybrid",
        }

    def architecture_profile(self) -> dict[str, Any]:
        return {
            "rhythm": "3:1",
            "tract": "gated_deltanet",
            "bridge": "gated_attention",
        }

    def propose_action(self, task: str, context: list[dict[str, Any]]) -> dict[str, Any]:
        _ = context
        if task == "draft_claim_denial_email":
            return {
                "type": "draft_claim_denial_email",
                "customer_impact": True,
                "financial_consequence": True,
                "binding_effect": False,
            }
        return {
            "type": "unknown_action",
            "customer_impact": False,
            "financial_consequence": False,
            "binding_effect": False,
        }


register_adapter("qwen35", Qwen35Adapter)
