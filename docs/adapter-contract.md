# Adapter Contract

BLKBX Lab adapters provide action metadata and model identity to the public trace and demo flows.

## ModelAdapter Protocol

```python
class ModelAdapter(Protocol):
    def model_info(self) -> dict[str, Any]: ...
    def architecture_profile(self) -> dict[str, Any]: ...
    def propose_action(self, task: str, context: list[dict[str, Any]]) -> dict[str, Any]: ...
```

## Minimum Model Metadata

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

## Installed Public Adapter

- `qwen35`

## Current Scope

- Adapter lookup is currently based on registered adapter names.
- The public release surface does not yet promise a stable family-to-adapter or model-to-adapter mapping layer.
- Additional runtimes should not be documented as supported until they are registered in `adapters/` and exercised by the public contract tests.
