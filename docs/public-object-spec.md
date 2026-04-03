# mech-lab Public Object Spec

Release-facing identity:

- product repo: `mech-lab`
- published package: `mechlab-sdk`
- CLI: `mechlab`
- Python namespace: `mech_lab`

## EvidenceBundle

Minimum fields:
- `trace_id`
- `manifest_path`
- `output_dir`
- `bundle_digest`
- `summary`
- `report`
- `receipt_path` when present
- `report_kinds`

Example:

```json
{
  "trace_id": "trace-sdk-docs",
  "manifest_path": "artifacts/mechlab-demo/mair_manifest.v1.json",
  "output_dir": "artifacts/mechlab-demo",
  "bundle_digest": "3e5f1a9b0c2d4411",
  "receipt_path": null,
  "report_kinds": ["release-summary", "compression-forgetting", "tract-vs-bridge", "bridge-necessity"],
  "summary": {
    "trace_id": "trace-sdk-docs",
    "model_family": "qwen3.5-hybrid",
    "topology_backend": "exact_persistence"
  }
}
```

## AnalysisResult

Adds:
- `profile`
- analyzed summary with hook validation and report kinds

Example:

```json
{
  "trace_id": "trace-sdk-docs",
  "manifest_path": "artifacts/mechlab-demo/mair_manifest.v1.json",
  "profile": "qwen3.5-hybrid",
  "receipt_path": "artifacts/mechlab-demo/assurance_receipt.v1.json",
  "summary": {
    "hook_validation": {
      "required": ["pre-D1", "post-D1", "post-D2", "post-D3", "post-attention", "block-output"],
      "missing": [],
      "passed": true
    }
  }
}
```

## ComparisonPacket

Minimum fields:
- `comparison_path`
- `output_dir`
- `left_manifest_path`
- `right_manifest_path`
- `summary`
- `report`

Example:

```json
{
  "comparison_path": "artifacts/compare/backend_comparison.v1.json",
  "left_manifest_path": "run-a/mair_manifest.v1.json",
  "right_manifest_path": "run-b/mair_manifest.v1.json",
  "summary": {
    "left_trace_id": "trace-left",
    "right_trace_id": "trace-right",
    "backend_pair": ["mock", "mock"],
    "schema_match": true,
    "bridge_dependence_delta": 0.0,
    "tract_retention_delta": 0.0,
    "topology_distance": 0.0
  }
}
```

## ReceiptResult

Minimum fields:
- `trace_id`
- `receipt_path`
- `manifest_path`
- `decision`
- `summary`
- `report`

Example:

```json
{
  "trace_id": "trace-sdk-docs",
  "receipt_path": "artifacts/mechlab-demo/assurance_receipt.v1.json",
  "manifest_path": "artifacts/mechlab-demo/mair_manifest.v1.json",
  "decision": "pass",
  "summary": {
    "passed": ["manifest_valid", "has_topology_summary"],
    "failed": [],
    "notes": []
  }
}
```

## Contract rules

- `to_dict()` is required on all four public object types.
- Public objects expose only MAIR-backed artifact paths or rendered summaries.
- Public examples should never require callers to inspect raw BLT-native rows directly.
