from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BUILTIN_PROFILE_FILES = {
    "qwen3.5-2b": "qwen3.5-2b.profile.json",
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def config_root() -> Path:
    packaged = Path(__file__).resolve().parent / "configs"
    if packaged.exists():
        return packaged
    return repo_root() / "configs"


def builtin_profile_path(name: str = "qwen3.5-2b") -> Path:
    try:
        filename = BUILTIN_PROFILE_FILES[name]
    except KeyError as exc:
        raise KeyError(f"unknown BLT profile: {name}") from exc
    return config_root() / filename


def load_profile(profile: str | Path | dict[str, Any] | None, *, backend: str) -> dict[str, Any]:
    if isinstance(profile, dict):
        return profile

    if profile is None:
        if backend == "qwen_hybrid_hf":
            profile_path = builtin_profile_path()
        else:
            return {}
    else:
        profile_path = Path(profile)
        if not profile_path.exists():
            profile_path = builtin_profile_path(str(profile))

    return json.loads(profile_path.read_text(encoding="utf-8"))
