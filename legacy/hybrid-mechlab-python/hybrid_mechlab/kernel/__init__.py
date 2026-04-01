"""NumPy-first math kernel for hybrid-mechlab."""

from hybrid_mechlab.kernel.backend import MathKernelBackend, get_math_backend
from hybrid_mechlab.kernel.graph import Graph
from hybrid_mechlab.kernel.persistence import (
    BirthDeathPair,
    PersistenceComparison,
    PersistenceDiagram,
    PersistenceInput,
    PersistenceReport,
    PersistenceSummary,
)
from hybrid_mechlab.kernel.sheaf import GluingReport, PartialSection, PartialSheaf
from hybrid_mechlab.kernel.simplicial import SimplicialComplex, Simplex
from hybrid_mechlab.kernel.sparse import SparseBatch, SparseVector
from hybrid_mechlab.kernel.topology import SignedSketch
from hybrid_mechlab.kernel.transport import TransportState, TransportSummary

__all__ = [
    "BirthDeathPair",
    "GluingReport",
    "Graph",
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
