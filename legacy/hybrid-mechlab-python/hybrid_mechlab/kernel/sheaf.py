"""Sheaf-style aggregation helpers for sparse trace sections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class PartialSection:
    id: int
    value: Any


@dataclass(frozen=True)
class GluingReport:
    defect_score: float
    sections: tuple[PartialSection, ...]


@dataclass(frozen=True)
class PartialSheaf:
    sections: tuple[PartialSection, ...]
    defect_score: float

    def gluing_report(self) -> GluingReport:
        return GluingReport(defect_score=self.defect_score, sections=self.sections)


def build_partial_sheaf(
    sparse_codes: Sequence[dict[str, Any]],
    *,
    basis: str,
    cancellation_pairs: int,
) -> PartialSheaf:
    sections = tuple(
        PartialSection(id=idx, value={"basis": basis, "hook": code["hook"]})
        for idx, code in enumerate(sparse_codes)
    )
    if not sections:
        return PartialSheaf(sections=tuple(), defect_score=0.0)
    defect_score = min(1.0, cancellation_pairs / max(len(sections), 1))
    return PartialSheaf(sections=sections, defect_score=defect_score)
