from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import re
from typing import Any, cast

from .profiles import load_profile
from .runtime import NativeQwenPreflightError, inspect_native_qwen_runtime

STAGES = ("pre_d1", "post_d1", "post_d2", "post_d3", "post_attention", "block_output")


class CaptureError(RuntimeError):
    pass


def tokenize_prompt(prompt: str) -> list[str]:
    tokens = [token for token in re.findall(r"\w+|[^\w\s]", prompt) if token.strip()]
    return tokens or ["<empty>"]


def _float_seed(*parts: object) -> float:
    digest = sha256(":".join(str(part) for part in parts).encode("utf-8")).hexdigest()
    raw = int(digest[:12], 16)
    return (raw / float(0xFFFFFFFFFFFF)) * 2.0 - 1.0


def _vector(seed: str, width: int) -> list[float]:
    return [round(_float_seed(seed, idx), 6) for idx in range(width)]


def _build_mock_trace(
    prompt: str,
    trace_id: str,
    *,
    model_family: str = "qwen3.5-hybrid",
    model_variant: str = "mock-2b",
    block_count: int = 4,
    width: int = 8,
) -> dict[str, Any]:
    tokens = tokenize_prompt(prompt)
    blocks: list[dict[str, Any]] = []
    for block_index in range(block_count):
        block_id = f"block-{block_index}"
        token_records: list[dict[str, Any]] = []
        for token_index, token in enumerate(tokens):
            stage_vectors = {
                stage: _vector(f"{trace_id}:{block_id}:{token_index}:{token}:{stage}", width)
                for stage in STAGES
            }
            token_records.append(
                {
                    "token_index": token_index,
                    "token": token,
                    "stages": stage_vectors,
                }
            )
        blocks.append({"block_id": block_id, "token_records": token_records})
    return {
        "trace_id": trace_id,
        "prompt": prompt,
        "tokens": tokens,
        "model_family": model_family,
        "model_variant": model_variant,
        "block_count": block_count,
        "width": width,
        "blocks": blocks,
    }


def _iter_blocks(model: Any) -> list[Any]:
    if hasattr(model, "model") and hasattr(model.model, "layers"):
        return list(model.model.layers)
    if hasattr(model, "model") and hasattr(model.model, "language_model") and hasattr(model.model.language_model, "layers"):
        return list(model.model.language_model.layers)
    if hasattr(model, "language_model") and hasattr(model.language_model, "layers"):
        return list(model.language_model.layers)
    if hasattr(model, "text_model") and hasattr(model.text_model, "layers"):
        return list(model.text_model.layers)
    if hasattr(model, "transformer") and hasattr(model.transformer, "h"):
        return list(model.transformer.h)
    raise CaptureError("unsupported model architecture for hybrid block enumeration")


def _extract_tensor(payload: Any) -> Any:
    if isinstance(payload, tuple):
        return payload[0]
    return payload


def _resolve_torch_dtype(name: str):
    import torch

    lookup: dict[str, Any] = {
        "float16": getattr(torch, "float16"),
        "bfloat16": getattr(torch, "bfloat16"),
        "float32": getattr(torch, "float32"),
        "auto": None,
    }
    try:
        return lookup[name]
    except KeyError as exc:
        raise CaptureError(f"unsupported dtype in BLT profile: {name}") from exc


def _resolve_device(name: str) -> str:
    if name != "auto":
        return name
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) is not None and torch.backends.mps.is_available():
            return "mps"
        return "cpu"
    except Exception:
        return "cpu"


@lru_cache(maxsize=2)
def _load_qwen_backend(model_id: str, device: str, dtype_name: str):
    try:
        import torch
        from transformers import AutoConfig, AutoModelForCausalLM, AutoModelForImageTextToText, AutoTokenizer
    except Exception as exc:  # pragma: no cover - exercised in integration usage
        raise CaptureError(
            "qwen_hybrid_hf backend requires torch and transformers. "
            "Install them from the repo root with "
            "python -m pip install -e './internal/trace/legacy_blt[model]'"
        ) from exc

    try:
        inspect_native_qwen_runtime(model_id=model_id)
    except NativeQwenPreflightError as exc:
        raise CaptureError(f"native qwen3_5 preflight failed for {model_id}: {exc}") from exc

    dtype = _resolve_torch_dtype(dtype_name)
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token
    config = AutoConfig.from_pretrained(model_id)
    architectures = tuple(getattr(config, "architectures", ()) or ())
    kwargs: dict[str, Any] = {}
    if dtype is not None:
        kwargs["torch_dtype"] = dtype
    kwargs["low_cpu_mem_usage"] = True
    if hasattr(config, "text_config") or any("ConditionalGeneration" in item for item in architectures):
        model = AutoModelForImageTextToText.from_pretrained(model_id, **kwargs)
    else:
        model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)
    resolved_device = _resolve_device(device)
    model = cast(Any, model)
    model.to(resolved_device)
    model.eval()
    torch.manual_seed(0)
    getattr(torch, "set_num_threads")(1)
    return tokenizer, model, resolved_device


def resolve_stage_plan(model: Any, profile: dict[str, Any]) -> list[dict[str, Any]]:
    capture = profile.get("capture") or {}
    block_size = int(capture.get("block_size", 4))
    block_start = int(capture.get("block_start", 0))
    block_limit = capture.get("block_limit")
    selectors = capture.get("stage_selectors") or {}
    if not selectors:
        raise CaptureError("BLT profile is missing capture.stage_selectors")

    stage_offsets: dict[str, int] = {}
    for stage in STAGES:
        selector = selectors.get(stage)
        if selector is None:
            raise CaptureError(f"BLT profile is missing stage selector: {stage}")
        kind = selector.get("kind")
        expected_kind = "layer_input" if stage == "pre_d1" else "layer_output"
        if kind != expected_kind:
            raise CaptureError(
                f"stage selector {stage} must use kind={expected_kind}, got kind={kind}"
            )
        offset = int(selector.get("offset", -1))
        if offset < 0 or offset >= block_size:
            raise CaptureError(
                f"stage selector {stage} offset {offset} is invalid for block_size={block_size}"
            )
        stage_offsets[stage] = offset

    blocks = _iter_blocks(model)
    total_layers = len(blocks)
    available_layers = total_layers - block_start
    if available_layers < block_size:
        raise CaptureError(
            f"model has {total_layers} layers; BLT profile requires at least {block_start + block_size}"
        )

    max_blocks = available_layers // block_size
    if block_limit is not None:
        max_blocks = min(max_blocks, int(block_limit))
    if max_blocks <= 0:
        raise CaptureError("BLT profile resolved to zero hybrid blocks")

    stage_plan: list[dict[str, Any]] = []
    for block_index in range(max_blocks):
        base_index = block_start + (block_index * block_size)
        stage_plan.append(
            {
                "block_id": f"block-{block_index}",
                "base_index": base_index,
                "stage_indices": {
                    stage: base_index + offset for stage, offset in stage_offsets.items()
                },
            }
        )
    return stage_plan


def _tensor_vector(tensor: Any, token_index: int, width: int) -> list[float]:
    vector = tensor[0, token_index, :width].detach().cpu().tolist()
    return [round(float(value), 6) for value in vector]


def _build_trace_from_tensors(
    *,
    trace_id: str,
    prompt: str,
    tokens: list[str],
    captured_stages: dict[str, dict[str, Any]],
    profile: dict[str, Any],
    model_family: str | None,
    model_variant: str | None,
) -> dict[str, Any]:
    capture = profile.get("capture") or {}
    width = int(capture.get("vector_width", 8))
    blocks: list[dict[str, Any]] = []
    for block_id, stage_map in captured_stages.items():
        token_records = []
        for token_index, token in enumerate(tokens):
            token_records.append(
                {
                    "token_index": token_index,
                    "token": token,
                    "stages": {
                        stage: _tensor_vector(stage_map[stage], token_index, width)
                        for stage in STAGES
                    },
                }
            )
        blocks.append({"block_id": block_id, "token_records": token_records})

    return {
        "trace_id": trace_id,
        "prompt": prompt,
        "tokens": tokens,
        "model_family": model_family or str(profile.get("model_family", "qwen3.5-hybrid")),
        "model_variant": model_variant or str(profile.get("model_variant", profile.get("model_id", "qwen-hybrid"))),
        "capture_backend": "qwen_hybrid_hf",
        "profile_id": str(profile.get("profile_id", "unknown-profile")),
        "block_count": len(blocks),
        "width": width,
        "blocks": blocks,
    }


def _build_qwen_hybrid_trace(
    prompt: str,
    trace_id: str,
    *,
    profile: dict[str, Any],
    model_family: str | None = None,
    model_variant: str | None = None,
) -> dict[str, Any]:
    runtime = profile.get("runtime") or {}
    device = str(runtime.get("device", "auto"))
    dtype = str(runtime.get("dtype", "float32"))
    max_length = int(runtime.get("max_length", 512))
    tokenizer, model, resolved_device = _load_qwen_backend(str(profile["model_id"]), device, dtype)

    import torch

    encoded = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_length)
    encoded = {key: value.to(resolved_device) for key, value in encoded.items()}
    tokens = tokenizer.convert_ids_to_tokens(encoded["input_ids"][0].detach().cpu().tolist())
    stage_plan = resolve_stage_plan(model, profile)

    pre_inputs: dict[int, Any] = {}
    layer_outputs: dict[int, Any] = {}
    block_modules = _iter_blocks(model)
    handles = []

    def make_pre_hook(layer_index: int):
        def _pre_hook(_module, inputs):
            pre_inputs[layer_index] = _extract_tensor(inputs[0]).detach().cpu()

        return _pre_hook

    def make_output_hook(layer_index: int):
        def _hook(_module, _inputs, output):
            layer_outputs[layer_index] = _extract_tensor(output).detach().cpu()

        return _hook

    pre_layers = sorted({item["stage_indices"]["pre_d1"] for item in stage_plan})
    output_layers = sorted(
        {
            index
            for item in stage_plan
            for stage, index in item["stage_indices"].items()
            if stage != "pre_d1"
        }
    )

    try:
        for layer_index in pre_layers:
            handles.append(block_modules[layer_index].register_forward_pre_hook(make_pre_hook(layer_index)))
        for layer_index in output_layers:
            handles.append(block_modules[layer_index].register_forward_hook(make_output_hook(layer_index)))
        with torch.no_grad():
            model(**encoded, use_cache=False)
    finally:
        for handle in handles:
            handle.remove()

    captured_stages: dict[str, dict[str, Any]] = {}
    for item in stage_plan:
        block_id = str(item["block_id"])
        stage_indices = item["stage_indices"]
        stage_map: dict[str, Any] = {}
        pre_index = stage_indices["pre_d1"]
        if pre_index not in pre_inputs:
            raise CaptureError(f"missing pre_d1 capture for {block_id}")
        stage_map["pre_d1"] = pre_inputs[pre_index]
        for stage in STAGES:
            if stage == "pre_d1":
                continue
            layer_index = stage_indices[stage]
            if layer_index not in layer_outputs:
                raise CaptureError(f"missing {stage} capture for {block_id}")
            stage_map[stage] = layer_outputs[layer_index]
        captured_stages[block_id] = stage_map

    trace = _build_trace_from_tensors(
        trace_id=trace_id,
        prompt=prompt,
        tokens=tokens,
        captured_stages=captured_stages,
        profile=profile,
        model_family=model_family,
        model_variant=model_variant or str(profile["model_id"]),
    )
    trace["runtime"] = {
        "device": resolved_device,
        "dtype": dtype,
        "profile_path": profile.get("_profile_path"),
    }
    return trace


def build_trace(
    prompt: str,
    trace_id: str,
    *,
    backend: str = "mock",
    profile: str | Path | dict[str, Any] | None = None,
    model_family: str | None = None,
    model_variant: str | None = None,
    block_count: int = 4,
    width: int = 8,
) -> dict[str, Any]:
    if backend == "mock":
        return _build_mock_trace(
            prompt,
            trace_id,
            model_family=model_family or "qwen3.5-hybrid",
            model_variant=model_variant or "mock-2b",
            block_count=block_count,
            width=width,
        )
    if backend == "qwen_hybrid_hf":
        loaded_profile = load_profile(profile, backend=backend)
        if isinstance(profile, (str, Path)):
            loaded_profile["_profile_path"] = str(Path(profile))
        elif profile is None:
            loaded_profile["_profile_path"] = None
        return _build_qwen_hybrid_trace(
            prompt,
            trace_id,
            profile=loaded_profile,
            model_family=model_family,
            model_variant=model_variant,
        )
    raise CaptureError(f"unknown BLT capture backend: {backend}")
