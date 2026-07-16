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

- Registered adapter names remain canonical for the public surface.
- Shipped Qwen selectors `qwen35`, `qwen3.5`, `qwen3.5-2b`, and `Qwen/Qwen3.5-2B` resolve to the installed `qwen35` adapter.
- Unsupported `family` or `model` values fail with a clear supported-adapters error.
- Additional runtimes should not be documented as supported until they are registered under `python/blkbx_lab/adapters/` and exercised by the public contract tests.
