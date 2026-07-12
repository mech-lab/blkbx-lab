# Adapter Contract

BLKBX Lab requires action metadata, not activation access.

## ModelAdapter Protocol

```python
class ModelAdapter(Protocol):
    def model_info(self) -> dict: ...
    def architecture_profile(self) -> dict: ...
    def propose_action(self, task: str, context: list[dict]) -> dict: ...
```

## Minimum model metadata

```json
{
  "model_id": "Qwen/Qwen3.5-2B",
  "provider": "qwen",
  "runtime": "transformers",
  "architecture_family": "gated_deltanet_hybrid",
  "architecture_profile": {
    "rhythm": "3:1",
    "tract": "gated_deltanet",
    "bridge": "gated_attention"
  }
}
```

## Supported Runtimes

- Qwen3.5 (native)
- vLLM (via OpenAI compatible endpoint)
- SGLang (via OpenAI compatible endpoint)
