"""NumPy-first math kernel for hybrid-mechlab."""

from .backend import MathKernelBackend, get_math_backend
from .geometry import GeodesicPath, GeodesicSegment, Holonom, HolonomRisk
from .graph import Graph
from .persistence import (
    BirthDeathPair,
    PersistenceComparison,
    PersistenceDiagram,
    PersistenceInput,
    PersistenceReport,
    PersistenceSummary,
)
from .sheaf import GluingReport, PartialSection, PartialSheaf
from .simplicial import SimplicialComplex, Simplex
from .sparse import SparseBatch, SparseVector
from .topology import SignedSketch
from .transport import TransportState, TransportSummary

__all__ = [
    "BirthDeathPair",
    "GeodesicPath",
    "GeodesicSegment",
    "GluingReport",
    "Graph",
    "Holonom",
    "HolonomRisk",
    "MathKernelBackend",
    "PartialSection",
    "PartialSheaf",
    "PersistenceComparison",
    "PersistenceDiagram",
    "PersistenceInput",
    "PersistenceReport",
    "PersistenceSummary",
    "SignedSketch",
    "Simplex",
    "SimplicialComplex",
    "SparseBatch",
    "SparseVector",
    "TransportState",
    "TransportSummary",
    "get_math_backend",
]
