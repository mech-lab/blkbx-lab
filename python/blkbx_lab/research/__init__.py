"""Opt-in research helpers for the umbrella mechlab-sdk install."""

from __future__ import annotations

from importlib.util import find_spec

EXTRA_NAME = "research"
OPTIONAL_DEPENDENCIES = ("markdown_it",)
AVAILABLE_MODULES = ("actuarial",)


def dependency_status() -> dict[str, bool]:
    return {dependency: find_spec(dependency) is not None for dependency in OPTIONAL_DEPENDENCIES}


def available() -> bool:
    return all(dependency_status().values())


def require_dependencies() -> None:
    missing = [dependency for dependency, present in dependency_status().items() if not present]
    if missing:
        names = ", ".join(missing)
        raise ModuleNotFoundError(
            f"Research helpers require the `{EXTRA_NAME}` extra. Install with `pip install \"mechlab-sdk[{EXTRA_NAME}]\"`. Missing modules: {names}."
        )


def describe() -> dict[str, object]:
    return {
        "extra": EXTRA_NAME,
        "dependencies": list(OPTIONAL_DEPENDENCIES),
        "modules": list(AVAILABLE_MODULES),
        "available": available(),
        "scope": "Research helpers and reproducibility-side tooling stay outside the default install contract.",
    }


__all__ = [
    "AVAILABLE_MODULES",
    "EXTRA_NAME",
    "OPTIONAL_DEPENDENCIES",
    "available",
    "dependency_status",
    "describe",
    "require_dependencies",
]
