from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = REPO_ROOT.parent
INTERNAL_MAIR_SRC = REPO_ROOT / "internal" / "ink" / "legacy_mair" / "src"
INTERNAL_BLT_SRC = REPO_ROOT / "internal" / "trace" / "legacy_blt" / "src"
LEGACY_MAIR_SRC = WORKSPACE_ROOT / "MAIR" / "src"
LEGACY_BLT_SRC = WORKSPACE_ROOT / "BLT" / "src"


def candidate_paths() -> tuple[Path, ...]:
    return (
        REPO_ROOT,
        INTERNAL_MAIR_SRC,
        INTERNAL_BLT_SRC,
        LEGACY_MAIR_SRC,
        LEGACY_BLT_SRC,
    )


def ensure_workspace_imports() -> list[str]:
    inserted: list[str] = []
    for path in reversed(candidate_paths()):
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))
            inserted.append(str(path))
    return inserted


def repo_availability() -> dict[str, bool]:
    bundled_mair = INTERNAL_MAIR_SRC.exists()
    bundled_blt = INTERNAL_BLT_SRC.exists()
    legacy_mair = LEGACY_MAIR_SRC.exists()
    legacy_blt = LEGACY_BLT_SRC.exists()
    return {
        "hybrid_mechlab": REPO_ROOT.exists(),
        "mair_repo": bundled_mair or legacy_mair,
        "blt_repo": bundled_blt or legacy_blt,
        "bundled_mair_repo": bundled_mair,
        "bundled_blt_repo": bundled_blt,
        "legacy_mair_repo": legacy_mair,
        "legacy_blt_repo": legacy_blt,
    }


def import_optional(module_name: str) -> tuple[ModuleType | None, str | None]:
    ensure_workspace_imports()
    try:
        return importlib.import_module(module_name), None
    except Exception as exc:  # pragma: no cover - exercised in integration usage
        return None, str(exc)


def require_module(module_name: str, hint: str) -> ModuleType:
    module, error = import_optional(module_name)
    if module is not None:
        return module
    raise ImportError(f"Unable to import {module_name}. {hint}. Root cause: {error}")


def module_version(module: ModuleType | None) -> str | None:
    if module is None:
        return None
    return getattr(module, "__version__", None)


def doctor_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    ensure_workspace_imports()

    repo_state = repo_availability()
    bundled_ready = repo_state.get("bundled_mair_repo", False) and repo_state.get(
        "bundled_blt_repo", False
    )
    legacy_ready = repo_state.get("legacy_mair_repo", False) and repo_state.get(
        "legacy_blt_repo", False
    )
    workspace_message = "Workspace fallbacks unavailable; rely on installed packages"
    if bundled_ready:
        workspace_message = "Bundled legacy trace and ink subsystem sources available"
    elif legacy_ready:
        workspace_message = "Legacy sibling BLT and MAIR repos available"
    checks.append(
        {
            "name": "workspace",
            "status": "ok" if repo_state["mair_repo"] and repo_state["blt_repo"] else "warning",
            "message": workspace_message,
            "fix": None,
        }
    )

    for module_name, hint in (
        ("hybrid_mechlab", "Install the unified blkbx-lab repo editable or run from the repository root"),
        ("mair", "Install the unified repo dependencies or ensure internal/ink/legacy_mair/src is importable"),
        ("blt", "Install the unified repo dependencies or ensure internal/trace/legacy_blt/src is importable"),
    ):
        module, error = import_optional(module_name)
        checks.append(
            {
                "name": module_name,
                "status": "ok" if module is not None else "missing",
                "message": f"{module_name} importable" if module is not None else error,
                "fix": None if module is not None else hint,
                "version": module_version(module),
            }
        )

    torch_module, torch_error = import_optional("torch")
    checks.append(
        {
            "name": "torch",
            "status": "ok" if torch_module is not None else "optional",
            "message": "Real model replay available" if torch_module is not None else torch_error,
            "fix": None if torch_module is not None else "Install BLT model extras for real replay backends",
            "version": module_version(torch_module),
        }
    )

    transformers_module, transformers_error = import_optional("transformers")
    transformers_version = module_version(transformers_module)
    transformers_ready = False
    transformers_message = transformers_error
    if transformers_module is not None:
        try:
            runtime_module = require_module(
                "blt.runtime",
                "Install the unified repo dependencies or ensure internal/trace/legacy_blt/src is importable",
            )
            preflight = runtime_module.inspect_native_qwen_runtime()
            transformers_ready = True
            transformers_message = (
                f"transformers {transformers_version} resolves {preflight['config_class']} "
                f"-> {preflight['model_class']}"
            )
        except Exception as exc:  # pragma: no cover - defensive import failure
            transformers_message = (
                f"transformers {transformers_version} failed native qwen preflight: {exc}"
            )
    checks.append(
        {
            "name": "transformers",
            "status": "ok" if transformers_ready else ("warning" if transformers_module is not None else "optional"),
            "message": transformers_message,
            "fix": (
                None
                if transformers_ready
                else "Install a Transformers build that recognizes model_type=qwen3_5 to enable qwen_hybrid_hf replay"
            ),
            "version": transformers_version,
        }
    )
    return checks
