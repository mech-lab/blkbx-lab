# Public Object Spec

BLKBX Lab exposes the following public objects for interacting with the SDK.

## ActionEvidenceBundle

```python
@dataclass(slots=True)
class ActionEvidenceBundle:
    action_id: str
    manifest_path: str
    output_dir: str
    summary: dict[str, Any]
    report: str
    evidence_hashes: list[str]
    receipt_path: str | None = None
```

## GateAnalysisResult

```python
@dataclass(slots=True)
class GateAnalysisResult:
    action_id: str
    manifest_path: str
    output_dir: str
    risk_tier: str
    required_controls: list[str]
    missing_controls: list[str]
    recommended_decision: str
    summary: dict[str, Any]
    report: str
```

## InkReceiptResult

```python
@dataclass(slots=True)
class InkReceiptResult:
    action_id: str
    receipt_path: str
    manifest_path: str
    decision: str
    summary: dict[str, Any]
    verification: dict[str, Any]
    report: str
```

## ReceiptComparisonPacket

```python
@dataclass(slots=True)
class ReceiptComparisonPacket:
    comparison_path: str
    output_dir: str
    left_receipt_path: str
    right_receipt_path: str
    summary: dict[str, Any]
    report: str
```
