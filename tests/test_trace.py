from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

pytest.importorskip("blt")
pytest.importorskip("mair.validate")

from blt.capture import CaptureError, build_trace, load_profile, resolve_stage_plan
from blt.export import run_trace
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


class FakeTokenizer:
    pad_token_id = 0
    eos_token_id = 0

    def __call__(self, prompt: str, return_tensors: str = "pt", truncation: bool = True, max_length: int = 512):  # noqa: ARG002
        token_count = max(1, len(prompt.split()))
        ids = torch.arange(1, token_count + 1).unsqueeze(0)
        return {"input_ids": ids, "attention_mask": torch.ones_like(ids)}

    def convert_ids_to_tokens(self, token_ids: list[int]) -> list[str]:
        return [f"tok_{token_id}" for token_id in token_ids]


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


def test_qwen_stage_plan_resolves_against_stub_model() -> None:
    model = FakeHybridModel()
    profile = load_profile("qwen3.5-2b", backend="qwen_hybrid_hf")
    plan = resolve_stage_plan(model, profile)
    assert len(plan) == 2
    assert plan[0]["stage_indices"]["pre_d1"] == 0
    assert plan[0]["stage_indices"]["post_attention"] == 3
    assert plan[1]["stage_indices"]["post_d2"] == 5


def test_qwen_backend_builds_trace_with_stub_model(monkeypatch: pytest.MonkeyPatch) -> None:
    model = FakeHybridModel()
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


def test_qwen_backend_fails_closed_for_invalid_stage_selector() -> None:
    model = FakeHybridModel()
    profile = deepcopy(load_profile("qwen3.5-2b", backend="qwen_hybrid_hf"))
    profile["capture"]["stage_selectors"]["post_attention"]["offset"] = 4
    with pytest.raises(CaptureError):
        resolve_stage_plan(model, profile)
