"""Opt-in experimental helpers for the umbrella mechlab-sdk install."""

from __future__ import annotations

from importlib.util import find_spec

EXTRA_NAME = "experimental"
OPTIONAL_DEPENDENCIES = ("rich",)


def dependency_status() -> dict[str, bool]:
    return {dependency: find_spec(dependency) is not None for dependency in OPTIONAL_DEPENDENCIES}


def available() -> bool:
    return all(dependency_status().values())


def require_dependencies() -> None:
    missing = [dependency for dependency, present in dependency_status().items() if not present]
    if missing:
        names = ", ".join(missing)
        raise ModuleNotFoundError(
            f"Experimental helpers require the `{EXTRA_NAME}` extra. Install with `pip install \"mechlab-sdk[{EXTRA_NAME}]\"`. Missing modules: {names}."
        )


def describe() -> dict[str, object]:
    return {
        "extra": EXTRA_NAME,
        "dependencies": list(OPTIONAL_DEPENDENCIES),
        "available": available(),
        "scope": "Experimental helpers remain opt-in even though the root wheel owns the public namespace.",
    }


__all__ = ["EXTRA_NAME", "OPTIONAL_DEPENDENCIES", "available", "dependency_status", "describe", "require_dependencies"]
