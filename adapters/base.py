from typing import Any, Protocol

class ModelAdapter(Protocol):
    def model_info(self) -> dict[str, Any]: ...
    def architecture_profile(self) -> dict[str, Any]: ...
    def propose_action(self, task: str, context: list[dict[str, Any]]) -> dict[str, Any]: ...

_ADAPTERS: dict[str, type[ModelAdapter]] = {}

def register_adapter(name: str, adapter_cls: type[ModelAdapter]) -> None:
    _ADAPTERS[name] = adapter_cls

def registered_adapter_names() -> tuple[str, ...]:
    return tuple(sorted(_ADAPTERS))

def get_adapter(name: str) -> ModelAdapter:
    adapter_cls = _ADAPTERS.get(name)
    if not adapter_cls:
        raise ValueError(f"Unknown adapter: {name}")
    return adapter_cls()
