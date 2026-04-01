"""Profile factories for native and reference transport families."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from hybrid_mechlab.schedules import (
    FamilyDescriptor,
    HybridSchedule,
    TransportFamilyKind,
    TransportRegimeKind,
    family_descriptor,
    ratio_schedule,
    schedule_from_sequence,
    validate_schedule,
)


class BackendKind(str, Enum):
    adapter = "adapter"
    native = "native"
    liger = "liger"


@dataclass(frozen=True)
class ResearchProfile:
    name: str
    family: FamilyDescriptor
    schedule: HybridSchedule
    backend: BackendKind
    hook_points: tuple[str, ...] = ()
    source_adapter: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def conformance(self):
        return validate_schedule(self.schedule)


class _NativeProfiles:
    def gated_deltanet(self) -> ResearchProfile:
        family = family_descriptor(TransportFamilyKind.gated_deltanet)
        schedule = ratio_schedule(3, 1, family=family, label="gated_deltanet")
        return ResearchProfile(
            name="native.gated_deltanet",
            family=family,
            schedule=schedule,
            backend=BackendKind.native,
            hook_points=("tract.local", "bridge.global"),
            metadata={"portfolio_lane": "native_core"},
        )

    def hgrn2(self) -> ResearchProfile:
        family = family_descriptor(TransportFamilyKind.hgrn2)
        schedule = ratio_schedule(2, 1, family=family, label="hgrn2")
        return ResearchProfile(
            name="native.hgrn2",
            family=family,
            schedule=schedule,
            backend=BackendKind.native,
            hook_points=("state.tract", "state.bridge"),
            metadata={"portfolio_lane": "native_core"},
        )

    def retnet(self) -> ResearchProfile:
        family = family_descriptor(TransportFamilyKind.retnet)
        schedule = ratio_schedule(
            4,
            1,
            family=family,
            label="retnet",
            local_kind=TransportRegimeKind.retention,
        )
        return ResearchProfile(
            name="native.retnet",
            family=family,
            schedule=schedule,
            backend=BackendKind.native,
            hook_points=("retention.window", "retention.bridge"),
            metadata={"portfolio_lane": "native_core"},
        )

    def hawk(self) -> ResearchProfile:
        family = family_descriptor(TransportFamilyKind.hawk)
        schedule = schedule_from_sequence(
            TransportFamilyKind.hawk,
            (
                TransportRegimeKind.recurrent_transport,
                TransportRegimeKind.gate,
                TransportRegimeKind.recurrent_transport,
                TransportRegimeKind.global_bridge,
            ),
            cadence_label="hawk-gated-4",
        )
        return ResearchProfile(
            name="native.hawk",
            family=family,
            schedule=schedule,
            backend=BackendKind.native,
            hook_points=("hawk.local", "hawk.gate", "hawk.bridge"),
            metadata={"portfolio_lane": "native_core"},
        )

    def transnormer_llm(self) -> ResearchProfile:
        family = family_descriptor(TransportFamilyKind.transnormer_llm)
        schedule = schedule_from_sequence(
            TransportFamilyKind.transnormer_llm,
            (
                TransportRegimeKind.local_attention,
                TransportRegimeKind.local_attention,
                TransportRegimeKind.norm,
                TransportRegimeKind.local_attention,
                TransportRegimeKind.global_bridge,
            ),
            cadence_label="transnormer-5",
        )
        return ResearchProfile(
            name="native.transnormer_llm",
            family=family,
            schedule=schedule,
            backend=BackendKind.native,
            hook_points=("local.attn", "local.norm", "global.bridge"),
            metadata={"portfolio_lane": "native_core"},
        )


class _ReferenceProfiles:
    def qwen35(self) -> ResearchProfile:
        family = family_descriptor(TransportFamilyKind.qwen35)
        schedule = ratio_schedule(3, 1, family=family, label="qwen35")
        return ResearchProfile(
            name="reference.qwen35",
            family=family,
            schedule=schedule,
            backend=BackendKind.adapter,
            hook_points=("block.recurrent", "block.bridge"),
            source_adapter="hybrid_mechlab.adapters.qwen35",
            metadata={"model_id": "Qwen/Qwen3.5-2B"},
        )

    def olmo_hybrid(self) -> ResearchProfile:
        family = family_descriptor(TransportFamilyKind.olmo_hybrid)
        schedule = ratio_schedule(4, 1, family=family, label="olmo_hybrid")
        return ResearchProfile(
            name="reference.olmo_hybrid",
            family=family,
            schedule=schedule,
            backend=BackendKind.adapter,
            hook_points=("block.local", "block.bridge"),
            source_adapter="hybrid_mechlab.adapters.olmo_hybrid",
        )

    def kimi_linear(self) -> ResearchProfile:
        family = family_descriptor(TransportFamilyKind.kimi_linear)
        schedule = ratio_schedule(
            2,
            1,
            family=family,
            label="kimi_linear",
            local_kind=TransportRegimeKind.retention,
        )
        return ResearchProfile(
            name="reference.kimi_linear",
            family=family,
            schedule=schedule,
            backend=BackendKind.adapter,
            hook_points=("block.linear", "block.bridge"),
            source_adapter="hybrid_mechlab.adapters.kimi_linear",
        )


native = _NativeProfiles()
reference = _ReferenceProfiles()


def all_native() -> tuple[ResearchProfile, ...]:
    return (
        native.gated_deltanet(),
        native.hgrn2(),
        native.retnet(),
        native.hawk(),
        native.transnormer_llm(),
    )


def all_reference() -> tuple[ResearchProfile, ...]:
    return (
        reference.qwen35(),
        reference.olmo_hybrid(),
        reference.kimi_linear(),
    )


def resolve_profile(
    family: str | TransportFamilyKind,
    backend: str | BackendKind,
) -> ResearchProfile:
    kind = family if isinstance(family, TransportFamilyKind) else TransportFamilyKind(family)
    selected = backend if isinstance(backend, BackendKind) else BackendKind(backend)

    native_map: dict[TransportFamilyKind, Callable[[], ResearchProfile]] = {
        TransportFamilyKind.gated_deltanet: native.gated_deltanet,
        TransportFamilyKind.hgrn2: native.hgrn2,
        TransportFamilyKind.retnet: native.retnet,
        TransportFamilyKind.hawk: native.hawk,
        TransportFamilyKind.transnormer_llm: native.transnormer_llm,
    }
    reference_map: dict[TransportFamilyKind, Callable[[], ResearchProfile]] = {
        TransportFamilyKind.qwen35: reference.qwen35,
        TransportFamilyKind.olmo_hybrid: reference.olmo_hybrid,
        TransportFamilyKind.kimi_linear: reference.kimi_linear,
    }

    if selected == BackendKind.native:
        return native_map[kind]()
    if selected == BackendKind.adapter:
        return reference_map[kind]()
    if kind == TransportFamilyKind.qwen35:
        profile = reference.qwen35()
    else:
        profile = native_map.get(kind, native.gated_deltanet)()
    return ResearchProfile(
        name=f"{profile.name}.liger",
        family=profile.family,
        schedule=profile.schedule,
        backend=BackendKind.liger,
        hook_points=profile.hook_points,
        source_adapter=profile.source_adapter,
        metadata={**profile.metadata, "migration_backend": "liger"},
    )
