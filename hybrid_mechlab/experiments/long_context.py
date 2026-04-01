"""Long-context benchmark harness for transport-heavy comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from hybrid_mechlab.api import HybridLab, TraceHandle
from hybrid_mechlab.profiles import ResearchProfile
from hybrid_mechlab.topology import metrics


@dataclass(frozen=True)
class LongContextCase:
    name: str
    prompt: str


@dataclass(frozen=True)
class LongContextResult:
    profile_name: str
    backend: str
    bridge_dependence: float
    tract_retention: float
    topology_drift: float


@dataclass(frozen=True)
class LongContextReport:
    wedge: str
    results: tuple[LongContextResult, ...]

    def best_retention_profile(self) -> str:
        return max(self.results, key=lambda item: item.tract_retention).profile_name


def run_long_context_benchmark(
    model: str,
    profiles: Iterable[ResearchProfile],
    *,
    cases: Iterable[LongContextCase] | None = None,
) -> LongContextReport:
    benchmark_cases = tuple(
        cases
        or (
            LongContextCase(
                name="entity_retention",
                prompt="Track a named entity across a long narrative and report the bridge dependencies.",
            ),
        )
    )
    prompts = tuple(case.prompt for case in benchmark_cases)
    results = []
    for profile in profiles:
        lab = HybridLab.attach(model=model, profile=profile, backend=profile.backend)
        trace: TraceHandle = lab.run(prompts=prompts, capture=("codes", "sketches", "transport"))
        results.append(
            LongContextResult(
                profile_name=profile.name,
                backend=profile.backend.value,
                bridge_dependence=metrics.bridge_dependence(trace),
                tract_retention=metrics.tract_retention(trace),
                topology_drift=metrics.topological_susceptibility(trace),
            )
        )
    return LongContextReport(wedge="long_context_reasoning", results=tuple(results))
