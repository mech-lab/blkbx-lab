"""Registry for transport families and profile factories."""

from __future__ import annotations

from typing import Callable

from hybrid_mechlab.profiles import ResearchProfile, all_native, all_reference


ProfileFactory = Callable[[], ResearchProfile]


def available_profiles() -> tuple[ResearchProfile, ...]:
    return (*all_native(), *all_reference())


def as_dict() -> dict[str, ResearchProfile]:
    return {profile.name: profile for profile in available_profiles()}
