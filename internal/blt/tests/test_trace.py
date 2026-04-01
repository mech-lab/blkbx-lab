from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

pytest.importorskip("blt")
pytest.importorskip("mair.validate")

from blt.capture import CaptureError, _load_qwen_backend, build_trace, load_profile, resolve_stage_plan
from blt.export import run_trace
from blt.runtime import NativeQwenPreflightError, inspect_native_qwen_runtime
from mair.validate import validate_manifest


class FakeLayer(torch.nn.Module):
    def __init__(self, layer_id: int) -> None:
        super().__init__()
        self.layer_id = layer_id

    def forward(self, x):
        return x + float(self.layer_id + 1)


class FakeHybridModel(torch.nn.Module):
    def __init__(self, layer_count: int = 8, hidden_size: int = 8) -> None:
        super().__init__()
        self.model = SimpleNamespace(layers=torch.nn.ModuleList([FakeLayer(idx) for idx in range(layer_count)]))
        self.config = SimpleNamespace(num_hidden_layers=layer_count, hidden_size=hidden_size)
        self.hidden_size = hidden_size

    def forward(self, input_ids, attention_mask=None, use_cache=False):  # noqa: ARG002
        x = input_ids.unsqueeze(-1).float().repeat(1, 1, self.hidden_size)
        for layer in self.model.layers:
            x = layer(x)
        return SimpleNamespace(last_hidden_state=x)


class FakeConditionalGenerationHybridModel(torch.nn.Module):
    def __init__(self, layer_count: int = 8, hidden_size: int = 8) -> None:
        super().__init__()
        language_model = SimpleNamespace(layers=torch.nn.ModuleList([FakeLayer(idx) for idx in range(layer_count)]))
        self.model = SimpleNamespace(language_model=language_model)
        self.config = SimpleNamespace(num_hidden_layers=layer_count, hidden_size=hidden_size)
        self.hidden_size = hidden_size

    def forward(self, input_ids, attention_mask=None, use_cache=False):  # noqa: ARG002
        x = input_ids.unsqueeze(-1).float().repeat(1, 1, self.hidden_size)
        for layer in self.model.language_model.layers:
            x = layer(x)
        return SimpleNamespace(last_hidden_state=x)


class FakeTokenizer:
    pad_token_id = 0
    eos_token_id = 0

    def __call__(self, prompt: str, return_tensors: str = "pt", truncation: bool = True, max_length: int = 512):  # noqa: ARG002
        token_count = max(1, len(prompt.split()))
        ids = torch.arange(1, token_count + 1).unsqueeze(0)
        return {"input_ids": ids, "attention_mask": torch.ones_like(ids)}

    def convert_ids_to_tokens(self, token_ids: list[int]) -> list[str]:
        return [f"tok_{token_id}" for token_id in token_ids]


def _fake_preflight_components(config_class, model_class, *, model_type: str = "qwen3_5"):
    class FakeAutoConfig:
        @staticmethod
        def from_pretrained(model_id: str):  # noqa: ARG004
            return config_class()

    class FakeAutoModelForImageTextToText:
        _model_mapping = object()

    def fake_get_model_class(config, mapping):  # noqa: ARG001
        assert isinstance(config, config_class)
        return model_class

    config_class.model_type = model_type
    return FakeAutoConfig, FakeAutoModelForImageTextToText, fake_get_model_class


def test_run_trace_writes_expected_artifacts(tmp_path: Path) -> None:
    manifest_path = run_trace("Paris answers itself.", "trace-blt-1", tmp_path, backend="mock")
    payload = validate_manifest(manifest_path)
    names = {artifact["artifact_type"] for artifact in payload["artifacts"]}
    assert {
        "mair_semantic_trace",
        "mair_graph_ir",
        "mair_numeric_lowering",
        "blt_codes",
        "tract_state_snapshot",
        "topology_summary",
    } <= names


def test_native_qwen_preflight_succeeds_with_native_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
    class Qwen3_5Config:
        __module__ = "transformers.models.qwen3_5.configuration_qwen3_5"

        def __init__(self) -> None:
            self.model_type = "qwen3_5"

    class Qwen3_5ForConditionalGeneration:
        __module__ = "transformers.models.qwen3_5.modeling_qwen3_5"

    monkeypatch.setattr(
        "blt.runtime._load_transformers_auto_components",
        lambda: _fake_preflight_components(Qwen3_5Config, Qwen3_5ForConditionalGeneration),
    )

    result = inspect_native_qwen_runtime()

    assert result["model_type"] == "qwen3_5"
    assert result["config_class"].endswith("Qwen3_5Config")
    assert result["model_class"].endswith("Qwen3_5ForConditionalGeneration")


def test_native_qwen_preflight_fails_when_config_load_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeAutoConfig:
        @staticmethod
        def from_pretrained(model_id: str):  # noqa: ARG004
            raise ValueError("missing qwen3_5 registration")

    class FakeAutoModelForImageTextToText:
        _model_mapping = object()

    monkeypatch.setattr(
        "blt.runtime._load_transformers_auto_components",
        lambda: (FakeAutoConfig, FakeAutoModelForImageTextToText, lambda *_args, **_kwargs: None),
    )

    with pytest.raises(NativeQwenPreflightError, match="AutoConfig.from_pretrained"):
        inspect_native_qwen_runtime()


def test_native_qwen_preflight_fails_when_resolution_lands_on_qwen3_next(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeQwen35Config:
        __module__ = "transformers.models.qwen3_5.configuration_qwen3_5"

        def __init__(self) -> None:
            self.model_type = "qwen3_5"

    class FakeQwen3NextForConditionalGeneration:
        __module__ = "transformers.models.qwen3_next.modeling_qwen3_next"

    monkeypatch.setattr(
        "blt.runtime._load_transformers_auto_components",
        lambda: _fake_preflight_components(FakeQwen35Config, FakeQwen3NextForConditionalGeneration),
    )

    with pytest.raises(NativeQwenPreflightError, match="qwen3_next"):
        inspect_native_qwen_runtime()


def test_native_qwen_preflight_fails_for_non_qwen35_model_class(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeQwen35Config:
        __module__ = "transformers.models.qwen3_5.configuration_qwen3_5"

        def __init__(self) -> None:
            self.model_type = "qwen3_5"

    class FakeQwen3ForConditionalGeneration:
        __module__ = "transformers.models.qwen3.modeling_qwen3"

    monkeypatch.setattr(
        "blt.runtime._load_transformers_auto_components",
        lambda: _fake_preflight_components(FakeQwen35Config, FakeQwen3ForConditionalGeneration),
    )

    with pytest.raises(NativeQwenPreflightError, match="expected auto-model class"):
        inspect_native_qwen_runtime()


def test_qwen_stage_plan_resolves_against_stub_model() -> None:
    model = FakeConditionalGenerationHybridModel()
    profile = load_profile("qwen3.5-2b", backend="qwen_hybrid_hf")
    plan = resolve_stage_plan(model, profile)
    assert len(plan) == 2
    assert plan[0]["stage_indices"]["pre_d1"] == 0
    assert plan[0]["stage_indices"]["post_attention"] == 3
    assert plan[1]["stage_indices"]["post_d2"] == 5


def test_qwen_backend_builds_trace_with_stub_model(monkeypatch: pytest.MonkeyPatch) -> None:
    model = FakeConditionalGenerationHybridModel()
    tokenizer = FakeTokenizer()
    monkeypatch.setattr("blt.capture._load_qwen_backend", lambda *args, **kwargs: (tokenizer, model, "cpu"))
    trace = build_trace(
        "Bridge tract topology test",
        "trace-real-1",
        backend="qwen_hybrid_hf",
        profile="qwen3.5-2b",
    )
    assert trace["capture_backend"] == "qwen_hybrid_hf"
    assert trace["block_count"] == 2
    assert trace["blocks"][0]["token_records"][0]["stages"]["post_d1"]


def test_qwen_backend_blocks_surrogate_runtime_before_model_load(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("transformers")
    _load_qwen_backend.cache_clear()

    def fail_preflight(*args, **kwargs):  # noqa: ARG001
        raise NativeQwenPreflightError(
            "auto-model resolution fell back to surrogate class "
            "transformers.models.qwen3_next.modeling_qwen3_next.Qwen3NextForConditionalGeneration"
        )

    monkeypatch.setattr("blt.capture.inspect_native_qwen_runtime", fail_preflight)

    with pytest.raises(CaptureError, match="native qwen3_5 preflight failed"):
        build_trace(
            "Bridge tract topology test",
            "trace-real-preflight",
            backend="qwen_hybrid_hf",
            profile="qwen3.5-2b",
        )

    _load_qwen_backend.cache_clear()


def test_qwen_backend_fails_closed_for_invalid_stage_selector() -> None:
    model = FakeHybridModel()
    profile = deepcopy(load_profile("qwen3.5-2b", backend="qwen_hybrid_hf"))
    profile["capture"]["stage_selectors"]["post_attention"]["offset"] = 4
    with pytest.raises(CaptureError):
        resolve_stage_plan(model, profile)
