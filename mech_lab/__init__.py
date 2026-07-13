from __future__ import annotations

import warnings

from blkbx_lab import (
    ActionEvidenceBundle,
    DoctorResult,
    GateAnalysisResult,
    InkReceiptResult,
    ReceiptComparisonPacket,
    analyze,
    compare,
    demo,
    doctor,
    explain,
    gate,
    report,
    tamper,
    trace,
    verify,
)

__all__ = [
    "analyze",
    "compare",
    "demo",
    "doctor",
    "explain",
    "gate",
    "report",
    "trace",
    "verify",
    "tamper",
    "ActionEvidenceBundle",
    "GateAnalysisResult",
    "InkReceiptResult",
    "ReceiptComparisonPacket",
    "DoctorResult",
]

warnings.warn(
    "The 'mech_lab' package is deprecated and will be removed in a future release. "
    "Please use 'blkbx_lab' instead.",
    DeprecationWarning,
    stacklevel=2,
)
