"""Public mech-lab SDK surface."""

from hybrid_mechlab._version import __version__

from mech_lab.api import analyze, compare, demo, doctor, explain, gate, report, trace
from mech_lab.objects import (
    AnalysisResult,
    ComparisonPacket,
    DoctorResult,
    EvidenceBundle,
    ReceiptResult,
)

__all__ = [
    "AnalysisResult",
    "ComparisonPacket",
    "DoctorResult",
    "EvidenceBundle",
    "ReceiptResult",
    "analyze",
    "compare",
    "demo",
    "doctor",
    "explain",
    "gate",
    "report",
    "trace",
    "__version__",
]
