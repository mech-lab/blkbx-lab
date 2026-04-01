"""Family-aware transport schedule helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Sequence


class TransportFamilyKind(str, Enum):
    gated_deltanet = "gated_deltanet"
    hgrn2 = "hgrn2"
    retnet = "retnet"
    hawk = "hawk"
    transnormer_llm = "transnormer_llm"
    olmo_hybrid = "olmo_hybrid"
    qwen35 = "qwen35"
    kimi_linear = "kimi_linear"
    custom = "custom"


class PortfolioLane(str, Enum):
    native_core = "native_core"
    understanding_first = "understanding_first"
    migration = "migration"


class TransportRegimeKind(str, Enum):
    recurrent_transport = "recurrent_transport"
    recurrent = "recurrent_transport"
    retention = "retention"
    local_attention = "local_attention"
    global_bridge = "global_bridge"
    bridge = "global_bridge"
    feedforward = "feedforward"
    norm = "norm"
    residual_add = "residual_add"
    residual = "residual_add"
    gate = "gate"
    migration = "migration"
    other = "other"


BlockOpKind = TransportRegimeKind


@dataclass(frozen=True)
class BridgeSpec:
    cadence: int
    label: str = "global_bridge"
    synchronizes_globally: bool = True
    strength: float = 1.0


@dataclass(frozen=True)
class FamilyDescriptor:
    kind: TransportFamilyKind
    lane: PortfolioLane
    name: str
    bridge: BridgeSpec | None = None
    notes: tuple[str, ...] = ()
    long_context_ready: bool = True


@dataclass(frozen=True)
class BlockOp:
    kind: TransportRegimeKind
    local_index: int
    repeats: int = 1
    label: str | None = None
    bridge: BridgeSpec | None = None


@dataclass(frozen=True)
class HybridSchedule:
    family: FamilyDescriptor
    ops: tuple[BlockOp, ...]
    cadence_label: str = "custom"

    def bridge_mask(self) -> list[bool]:
        return [op.kind == TransportRegimeKind.global_bridge for op in self.ops]

    def bridge_count(self) -> int:
        return sum(self.bridge_mask())

    def regime_counts(self) -> dict[TransportRegimeKind, int]:
        counts: dict[TransportRegimeKind, int] = {}
        for op in self.ops:
            counts[op.kind] = counts.get(op.kind, 0) + op.repeats
        return counts

    def summary(self) -> str:
        return (
            f"{self.family.name}: {len(self.ops)} ops, "
            f"{self.bridge_count()} bridges, cadence={self.cadence_label}"
        )


@dataclass(frozen=True)
class KernelConformanceReport:
    family: TransportFamilyKind
    passed: bool
    schedule_length: int
    bridge_count: int
    notes: tuple[str, ...] = field(default_factory=tuple)


def family_descriptor(kind: TransportFamilyKind) -> FamilyDescriptor:
    native = PortfolioLane.native_core
    ref = PortfolioLane.understanding_first
    descriptors = {
        TransportFamilyKind.gated_deltanet: FamilyDescriptor(
            kind=kind,
            lane=native,
            name="Gated DeltaNet",
            bridge=BridgeSpec(cadence=4, label="attention_bridge"),
            notes=("canonical native kernel", "first validation target"),
        ),
        TransportFamilyKind.hgrn2: FamilyDescriptor(
            kind=kind,
            lane=native,
            name="HGRN2",
            bridge=BridgeSpec(cadence=3, label="state_sync_bridge"),
            notes=("native kernel", "tests recurrent transport separation"),
        ),
        TransportFamilyKind.retnet: FamilyDescriptor(
            kind=kind,
            lane=native,
            name="RetNet",
            bridge=BridgeSpec(cadence=5, label="retention_bridge"),
            notes=("native kernel", "retention-focused transport family"),
        ),
        TransportFamilyKind.hawk: FamilyDescriptor(
            kind=kind,
            lane=native,
            name="Hawk",
            bridge=BridgeSpec(cadence=4, label="hawk_bridge"),
            notes=("native kernel", "gated recurrent transport"),
        ),
        TransportFamilyKind.transnormer_llm: FamilyDescriptor(
            kind=kind,
            lane=native,
            name="TransNormerLLM",
            bridge=BridgeSpec(cadence=5, label="norm_bridge"),
            notes=("native kernel", "local attention transport family"),
        ),
        TransportFamilyKind.qwen35: FamilyDescriptor(
            kind=kind,
            lane=ref,
            name="Qwen3.5",
            bridge=BridgeSpec(cadence=4, label="gated_attention_bridge"),
            notes=("reference proving ground", "first replay target"),
        ),
        TransportFamilyKind.olmo_hybrid: FamilyDescriptor(
            kind=kind,
            lane=ref,
            name="OLMo Hybrid",
            bridge=BridgeSpec(cadence=5, label="olmo_bridge"),
            notes=("reference profile", "validates generalization"),
        ),
        TransportFamilyKind.kimi_linear: FamilyDescriptor(
            kind=kind,
            lane=ref,
            name="Kimi Linear",
            bridge=BridgeSpec(cadence=3, label="kimi_bridge"),
            notes=("reference profile", "linear-memory schedule"),
        ),
        TransportFamilyKind.custom: FamilyDescriptor(
            kind=kind,
            lane=ref,
            name="Custom",
            notes=("user supplied schedule",),
        ),
    }
    return descriptors[kind]


def ratio_schedule(
    recurrent: int,
    bridge: int = 1,
    *,
    family: FamilyDescriptor | None = None,
    label: str | None = None,
    local_kind: TransportRegimeKind = TransportRegimeKind.recurrent_transport,
) -> HybridSchedule:
    """Construct a family-aware k:1 transport schedule."""

    if recurrent <= 0 or bridge <= 0:
        raise ValueError("recurrent and bridge counts must be positive")

    descriptor = family or family_descriptor(TransportFamilyKind.custom)
    bridge_spec = descriptor.bridge or BridgeSpec(cadence=recurrent + bridge)
    ops: list[BlockOp] = []
    local_idx = 0
    for i in range(recurrent):
        ops.append(
            BlockOp(
                kind=local_kind,
                local_index=local_idx,
                label=f"{label or descriptor.kind.value}.local.{i}",
            )
        )
        local_idx += 1
    for j in range(bridge):
        ops.append(
            BlockOp(
                kind=TransportRegimeKind.global_bridge,
                local_index=local_idx,
                label=f"{label or descriptor.kind.value}.bridge.{j}",
                bridge=bridge_spec,
            )
        )
        local_idx += 1
    return HybridSchedule(
        family=descriptor,
        ops=tuple(ops),
        cadence_label=f"{recurrent}:{bridge}",
    )


def custom_schedule(
    kinds: Iterable[TransportRegimeKind],
    *,
    family: FamilyDescriptor | None = None,
    cadence_label: str = "custom",
) -> HybridSchedule:
    """Build a schedule from an explicit iterable of regime kinds."""

    descriptor = family or family_descriptor(TransportFamilyKind.custom)
    ops = tuple(
        BlockOp(
            kind=kind,
            local_index=idx,
            label=f"{descriptor.kind.value}.{idx}",
            bridge=descriptor.bridge if kind == TransportRegimeKind.global_bridge else None,
        )
        for idx, kind in enumerate(kinds)
    )
    if not ops:
        raise ValueError("custom schedule must contain at least one op")
    return HybridSchedule(family=descriptor, ops=ops, cadence_label=cadence_label)


def validate_schedule(schedule: HybridSchedule) -> KernelConformanceReport:
    bridge_count = schedule.bridge_count()
    notes: list[str] = []
    passed = True
    if not schedule.ops:
        notes.append("schedule has no operations")
        passed = False
    if schedule.family.bridge is not None and bridge_count == 0:
        notes.append("descriptor expects a bridge but schedule has none")
        passed = False
    if schedule.family.lane == PortfolioLane.native_core and bridge_count == 0:
        notes.append("native family should expose at least one bridge op")
        passed = False
    if schedule.family.long_context_ready and len(schedule.ops) < 3:
        notes.append("long-context families should expose at least three ops")
        passed = False
    if passed:
        notes.append("schedule matches family descriptor expectations")
    return KernelConformanceReport(
        family=schedule.family.kind,
        passed=passed,
        schedule_length=len(schedule.ops),
        bridge_count=bridge_count,
        notes=tuple(notes),
    )


def schedule_from_sequence(
    family_kind: TransportFamilyKind,
    kinds: Sequence[TransportRegimeKind],
    *,
    cadence_label: str,
) -> HybridSchedule:
    return custom_schedule(
        kinds,
        family=family_descriptor(family_kind),
        cadence_label=cadence_label,
    )
