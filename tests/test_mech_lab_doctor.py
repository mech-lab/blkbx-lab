from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import mech_lab as ml
import mech_lab.api as ml_api
import mech_lab._workspace as workspace


def test_workspace_doctor_checks_use_native_qwen_preflight(monkeypatch) -> None:
    class FakeRuntimeModule:
        @staticmethod
        def inspect_native_qwen_runtime(model_id: str = "Qwen/Qwen3.5-2B") -> dict[str, str]:
            assert model_id == "Qwen/Qwen3.5-2B"
            return {
                "model_id": model_id,
                "model_type": "qwen3_5",
                "config_class": "transformers.models.qwen3_5.configuration_qwen3_5.Qwen3_5Config",
                "model_class": "transformers.models.qwen3_5.modeling_qwen3_5.Qwen3_5ForConditionalGeneration",
            }

    fake_modules = {
        "hybrid_mechlab": (SimpleNamespace(__version__="0.1.0a1"), None),
        "mair": (SimpleNamespace(__version__="0.1.0"), None),
        "blt": (SimpleNamespace(__version__="0.1.0"), None),
        "torch": (SimpleNamespace(__version__="2.11.0"), None),
        "transformers": (SimpleNamespace(__version__="5.5.0.dev0"), None),
        "blt.runtime": (FakeRuntimeModule(), None),
    }

    monkeypatch.setattr(workspace, "ensure_workspace_imports", lambda: [])
    monkeypatch.setattr(
        workspace,
        "repo_availability",
        lambda: {"hybrid_mechlab": True, "mair_repo": True, "blt_repo": True},
    )
    monkeypatch.setattr(workspace, "import_optional", lambda module_name: fake_modules[module_name])

    checks = {check["name"]: check for check in workspace.doctor_checks()}

    assert checks["transformers"]["status"] == "ok"
    assert "configuration_qwen3_5.Qwen3_5Config" in checks["transformers"]["message"]
    assert "modeling_qwen3_5.Qwen3_5ForConditionalGeneration" in checks["transformers"]["message"]


def test_doctor_keeps_demo_ready_when_native_qwen_preflight_fails(monkeypatch) -> None:
    qwen_profile_path = Path("/Volumes/128/BLT/configs/qwen3.5-2b.profile.json")

    fake_checks = [
        {"name": "workspace", "status": "ok", "message": "Sibling BLT/MAIR repos discovered", "fix": None},
        {"name": "hybrid_mechlab", "status": "ok", "message": "hybrid_mechlab importable", "fix": None, "version": "0.1.0a1"},
        {"name": "mair", "status": "ok", "message": "mair importable", "fix": None, "version": "0.1.0"},
        {"name": "blt", "status": "ok", "message": "blt importable", "fix": None, "version": "0.1.0"},
        {"name": "torch", "status": "ok", "message": "Real model replay available", "fix": None, "version": "2.11.0"},
        {
            "name": "transformers",
            "status": "warning",
            "message": "transformers 5.5.0.dev0 failed native qwen preflight: auto-model resolution fell back to surrogate class transformers.models.qwen3_next.modeling_qwen3_next.Qwen3NextForConditionalGeneration",
            "fix": "Install a Transformers build that recognizes model_type=qwen3_5 to enable qwen_hybrid_hf replay",
            "version": "5.5.0.dev0",
        },
    ]

    class FakeProfiles:
        @staticmethod
        def builtin_profile_path(name: str = "qwen3.5-2b") -> Path:
            assert name == "qwen3.5-2b"
            return qwen_profile_path

    monkeypatch.setattr(ml_api, "doctor_checks", lambda: fake_checks)
    monkeypatch.setattr(ml_api, "ensure_workspace_imports", lambda: [])
    monkeypatch.setattr(ml_api, "require_module", lambda *_args, **_kwargs: FakeProfiles)

    result = ml.doctor()

    assert result.demo_ready is True
    assert result.real_replay_ready is False
    assert "failed native qwen preflight" in result.report
