from __future__ import annotations

from typing import Any


QWEN35_MODEL_ID = "Qwen/Qwen3.5-2B"
QWEN35_MODEL_TYPE = "qwen3_5"
QWEN35_CONFIG_PREFIX = "transformers.models.qwen3_5."
QWEN35_MODEL_CLASS = "transformers.models.qwen3_5.modeling_qwen3_5.Qwen3_5ForConditionalGeneration"


class NativeQwenPreflightError(RuntimeError):
    pass


def _qualname(value: Any) -> str:
    module_name = getattr(value, "__module__", "<unknown>")
    object_name = getattr(value, "__name__", value.__class__.__name__)
    return f"{module_name}.{object_name}"


def _load_transformers_auto_components():
    try:
        from transformers import AutoConfig, AutoModelForImageTextToText
        from transformers.models.auto.auto_factory import _get_model_class
    except Exception as exc:  # pragma: no cover - exercised in integration usage
        raise NativeQwenPreflightError(
            "unable to import Transformers auto classes for native qwen3_5 preflight"
        ) from exc
    return AutoConfig, AutoModelForImageTextToText, _get_model_class


def inspect_native_qwen_runtime(model_id: str = QWEN35_MODEL_ID) -> dict[str, str]:
    AutoConfig, AutoModelForImageTextToText, get_model_class = _load_transformers_auto_components()

    try:
        config = AutoConfig.from_pretrained(model_id)
    except Exception as exc:  # pragma: no cover - exercised in integration usage
        raise NativeQwenPreflightError(
            f"AutoConfig.from_pretrained({model_id!r}) failed: {exc}"
        ) from exc

    config_class = _qualname(type(config))
    model_type = getattr(config, "model_type", None)
    if model_type != QWEN35_MODEL_TYPE:
        raise NativeQwenPreflightError(
            f"expected model_type={QWEN35_MODEL_TYPE}, got {model_type!r} from {config_class}"
        )
    if not config_class.startswith(QWEN35_CONFIG_PREFIX):
        raise NativeQwenPreflightError(
            f"expected native qwen3_5 config class under {QWEN35_CONFIG_PREFIX}, got {config_class}"
        )
    if "qwen3_next" in config_class.lower():
        raise NativeQwenPreflightError(f"config resolved to surrogate class {config_class}")

    try:
        model_class = get_model_class(config, AutoModelForImageTextToText._model_mapping)
    except Exception as exc:  # pragma: no cover - exercised in integration usage
        raise NativeQwenPreflightError(
            f"auto-model resolution failed for {model_id!r}: {exc}"
        ) from exc

    model_class_path = _qualname(model_class)
    if "qwen3_next" in model_class_path.lower():
        raise NativeQwenPreflightError(
            f"auto-model resolution fell back to surrogate class {model_class_path}"
        )
    if model_class_path != QWEN35_MODEL_CLASS:
        raise NativeQwenPreflightError(
            f"expected auto-model class {QWEN35_MODEL_CLASS}, got {model_class_path}"
        )

    return {
        "model_id": model_id,
        "model_type": str(model_type),
        "config_class": config_class,
        "model_class": model_class_path,
    }
