"""Primary Python API surface for hybrid-mechlab."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from hybrid_mechlab.io.manifests import TRACE_SCHEMA_KEYS, serialize_trace_record
from hybrid_mechlab.kernel.backend import get_math_backend
from hybrid_mechlab.kernel.schedule import analyze_schedule
from hybrid_mechlab.kernel.sparse import SparseBatch
from hybrid_mechlab.kernel.transport import backend_factor
from hybrid_mechlab.profiles import BackendKind, ResearchProfile, resolve_profile
from hybrid_mechlab.schedules import HybridSchedule, TransportFamilyKind
from hybrid_mechlab._version import RUST_CORE_VERSION, __version__


@dataclass(frozen=True)
class TransportDigest:
    local_steps: int
    bridge_crossings: int
    retention_score: float
    backend: str


@dataclass(frozen=True)
class SignedSketchRecord:
    positive_components: int
    negative_components: int
    cancellation_pairs: int
    cycle_hint: int


@dataclass(frozen=True)
class ReproducibilityManifest:
    model: str
    profile_name: str
    family: str
    backend: str
    schedule_hash: str
    rust_core_version: str = RUST_CORE_VERSION
    python_package_version: str = __version__


@dataclass(frozen=True)
class ComparisonReport:
    left_trace_id: str
    right_trace_id: str
    backend_pair: tuple[str, str]
    schema_match: bool
    bridge_dependence_delta_value: float
    tract_retention_delta_value: float

    def summary(self) -> str:
        return (
            f"compare {self.left_trace_id} vs {self.right_trace_id}: "
            f"schema_match={self.schema_match}, "
            f"bridge_delta={self.bridge_dependence_delta_value:.3f}, "
            f"retention_delta={self.tract_retention_delta_value:.3f}"
        )

    def bridge_dependence_delta(self) -> float:
        return self.bridge_dependence_delta_value

    def tract_retention_delta(self) -> float:
        return self.tract_retention_delta_value


class TopologyView:
    def __init__(self, trace: "TraceHandle") -> None:
        self._trace = trace

    def signed_sketches(self) -> SignedSketchRecord:
        return self._trace.signed_sketch

    def bridge_dependence(self) -> float:
        math = get_math_backend(self._trace.math_backend)
        return math.bridge_dependence(
            local_steps=self._trace.transport_digest.local_steps,
            bridge_crossings=self._trace.transport_digest.bridge_crossings,
        )

    def tract_retention(self) -> float:
        return self._trace.transport_digest.retention_score

    def summary(self) -> str:
        return (
            f"bridge_dependence={self.bridge_dependence():.3f}, "
            f"tract_retention={self.tract_retention():.3f}"
        )


@dataclass(frozen=True)
class TraceHandle:
    trace_id: str
    prompts: tuple[str, ...]
    profile: ResearchProfile
    backend: BackendKind
    math_backend: str
    schedule: HybridSchedule
    sparse_codes: tuple[dict[str, Any], ...]
    signed_sketch: SignedSketchRecord
    transport_digest: TransportDigest
    reproducibility_manifest: ReproducibilityManifest
    capture: tuple[str, ...]
    interventions: tuple[Any, ...]

    def summary(self) -> str:
        return (
            f"trace {self.trace_id}: {self.profile.family.name} via {self.backend.value}, "
            f"{len(self.prompts)} prompts, {self.schedule.bridge_count()} bridges"
        )

    def schema_keys(self) -> tuple[str, ...]:
        return TRACE_SCHEMA_KEYS

    def to_record(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "prompt_count": len(self.prompts),
            "profile_name": self.profile.name,
            "family": self.profile.family.kind.value,
            "backend": self.backend.value,
            "schedule": self.schedule.summary(),
            "capture": list(self.capture),
            "transport_digest": asdict(self.transport_digest),
            "signed_sketch": asdict(self.signed_sketch),
            "reproducibility_manifest": asdict(self.reproducibility_manifest),
            "sparse_codes": list(self.sparse_codes),
        }

    def topology(self) -> TopologyView:
        return TopologyView(self)

    def _signed_sketch(self):
        from hybrid_mechlab.kernel.topology import signed_sketch_from_counts

        return signed_sketch_from_counts(
            positive_components=self.signed_sketch.positive_components,
            negative_components=self.signed_sketch.negative_components,
            cancellation_pairs=self.signed_sketch.cancellation_pairs,
            cycle_hint=self.signed_sketch.cycle_hint,
        )

    def bridge_dependence(self) -> float:
        return self.topology().bridge_dependence()

    def tract_retention(self) -> float:
        return self.topology().tract_retention()

    def compare(self, other_trace: "TraceHandle") -> ComparisonReport:
        return ComparisonReport(
            left_trace_id=self.trace_id,
            right_trace_id=other_trace.trace_id,
            backend_pair=(self.backend.value, other_trace.backend.value),
            schema_match=self.schema_keys() == other_trace.schema_keys(),
            bridge_dependence_delta_value=self.bridge_dependence() - other_trace.bridge_dependence(),
            tract_retention_delta_value=self.tract_retention() - other_trace.tract_retention(),
        )


class HybridLab:
    """Entry point for attaching to a family/profile and running trace simulations."""

    def __init__(
        self,
        model: str,
        profile: ResearchProfile,
        *,
        backend: BackendKind,
        math_backend: str = "python",
        mode: str = "trace",
        family: TransportFamilyKind | None = None,
        **kwargs: Any,
    ) -> None:
        self.model = model
        self.profile = profile
        self.backend = backend
        self.math_backend = math_backend
        self.mode = mode
        self.family = family or profile.family.kind
        self.kwargs = kwargs
        self._last_trace: TraceHandle | None = None

    @classmethod
    def attach(
        cls,
        model: str,
        profile: ResearchProfile | None = None,
        *,
        family: str | TransportFamilyKind | None = None,
        backend: str | BackendKind = BackendKind.adapter,
        math_backend: str = "python",
        mode: str = "trace",
        **kwargs: Any,
    ) -> "HybridLab":
        selected_backend = backend if isinstance(backend, BackendKind) else BackendKind(backend)
        get_math_backend(math_backend)
        selected_profile = profile
        if selected_profile is None:
            if family is None:
                family = TransportFamilyKind.qwen35
            selected_profile = resolve_profile(family, selected_backend)
        return cls(
            model=model,
            profile=selected_profile,
            backend=selected_backend,
            math_backend=math_backend,
            mode=mode,
            family=selected_profile.family.kind,
            **kwargs,
        )

    def run(
        self,
        prompts: Iterable[str],
        capture: Sequence[str] | None = None,
        interventions: Sequence[Any] | None = None,
    ) -> TraceHandle:
        prompt_tuple = tuple(prompts)
        capture_tuple = tuple(capture or ("codes", "sketches", "transport"))
        intervention_tuple = tuple(interventions or ())
        trace = _build_trace(
            model=self.model,
            profile=self.profile,
            backend=self.backend,
            math_backend=self.math_backend,
            prompts=prompt_tuple,
            capture=capture_tuple,
            interventions=intervention_tuple,
        )
        self._last_trace = trace
        return trace

    def replace(self, replacement_policy: Any) -> "HybridLab":
        self.kwargs["replacement_policy"] = replacement_policy
        return self

    def export(self, path: str, format: str = "json") -> None:
        if self._last_trace is None:
            raise RuntimeError("run a trace before exporting")
        if format != "json":
            raise ValueError("only json export is implemented in the Python scaffold")
        record = serialize_trace_record(self._last_trace.to_record())
        Path(path).write_text(json.dumps(record, indent=2), encoding="utf-8")

    def topology(self) -> TopologyView:
        if self._last_trace is None:
            raise RuntimeError("run a trace before requesting topology")
        return self._last_trace.topology()

    def compare(self, other_trace: TraceHandle) -> ComparisonReport:
        if self._last_trace is None:
            raise RuntimeError("run a trace before comparing")
        return self._last_trace.compare(other_trace)


def _build_trace(
    *,
    model: str,
    profile: ResearchProfile,
    backend: BackendKind,
    math_backend: str,
    prompts: tuple[str, ...],
    capture: tuple[str, ...],
    interventions: tuple[Any, ...],
) -> TraceHandle:
    schedule = profile.schedule
    math = get_math_backend(math_backend)
    schedule_stats = analyze_schedule(schedule)
    summary = math.transport_summary(
        schedule_stats,
        prompt_count=len(prompts),
        backend_name=backend.value,
    )
    sketch = math.signed_sketch_from_counts(
        positive_components=summary.local_steps,
        negative_components=max(schedule_stats.bridge_count - 1, 0),
        cancellation_pairs=len(interventions),
        cycle_hint=max(schedule_stats.bridge_count - 1, 0),
    )
    sparse_batch = SparseBatch.from_rows(
        (
            ([idx, idx + 100], [backend_factor(backend.value), summary.retention_score])
            for idx, _hook in enumerate(profile.hook_points or ("transport.summary",))
        )
    )
    digest = TransportDigest(
        local_steps=summary.local_steps,
        bridge_crossings=summary.bridge_crossings,
        retention_score=summary.retention_score,
        backend=backend.value,
    )
    schedule_hash = hashlib.sha256(schedule.summary().encode("utf-8")).hexdigest()[:16]
    manifest = ReproducibilityManifest(
        model=model,
        profile_name=profile.name,
        family=profile.family.kind.value,
        backend=backend.value,
        schedule_hash=schedule_hash,
    )
    trace_hash = hashlib.sha256(
        "|".join((model, profile.name, backend.value, schedule_hash, *prompts)).encode("utf-8")
    ).hexdigest()[:12]
    return TraceHandle(
        trace_id=f"trace-{trace_hash}",
        prompts=prompts,
        profile=profile,
        backend=backend,
        math_backend=math_backend,
        schedule=schedule,
        sparse_codes=sparse_batch.to_trace_records(profile.hook_points or ("transport.summary",)),
        signed_sketch=SignedSketchRecord(**sketch.to_record()),
        transport_digest=digest,
        reproducibility_manifest=manifest,
        capture=capture,
        interventions=interventions,
    )
