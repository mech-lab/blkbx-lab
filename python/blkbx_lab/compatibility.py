from __future__ import annotations

import warnings

_SUPPORTED_ADAPTERS = {
    "qwen35": "qwen35",
    "qwen35-claims": "qwen35",
    "qwen3.5": "qwen35",
    "qwen/qwen3.5-2b": "qwen35",
}
_SUPPORTED_BACKENDS = {"mock", "adapter"}
_SUPPORTED_PROFILES = {"qwen3.5-hybrid"}

def reject_decorative_options(**kwargs: object) -> None:
    for name, value in kwargs.items():
        if value in (None, "", "default"):
            if value is not None:
                warnings.warn(
                    f"`{name}` is deprecated and ignored in the canonical v0.6 thin-waist flow.",
                    DeprecationWarning,
                    stacklevel=2,
                )
            continue
        if name == "backend" and isinstance(value, str) and value.casefold() in _SUPPORTED_BACKENDS:
            warnings.warn(
                f"`{name}` is deprecated and ignored in the canonical v0.6 thin-waist flow.",
                DeprecationWarning,
                stacklevel=2,
            )
            continue
        if name in {"family", "model"} and isinstance(value, str) and value.casefold() in _SUPPORTED_ADAPTERS:
            warnings.warn(
                f"`{name}` is deprecated and normalized to the `qwen35` deterministic demo adapter.",
                DeprecationWarning,
                stacklevel=2,
            )
            continue
        if name == "profile" and isinstance(value, str) and value.casefold() in _SUPPORTED_PROFILES:
            warnings.warn(
                f"`{name}` is deprecated and ignored in the canonical v0.6 thin-waist flow.",
                DeprecationWarning,
                stacklevel=2,
            )
            continue
        if name in {"adapter", "family", "model"}:
            raise ValueError("Supported public adapters: qwen35")
        raise ValueError(
            f"`{name}` is no longer a functional public option in the canonical trust path. "
            "Only the deterministic demo adapter is supported."
        )


def resolve_public_adapter(
    *,
    adapter: str | None = None,
    family: str | None = None,
    model: str | None = None,
) -> str:
    for candidate in (adapter, family, model):
        if candidate is None:
            continue
        normalized = _SUPPORTED_ADAPTERS.get(candidate.casefold())
        if normalized is not None:
            return normalized
        raise ValueError("Supported public adapters: qwen35")
    return "qwen35"
