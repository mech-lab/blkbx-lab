# Changelog

## [0.1.0a3] - Unreleased

### Added
- BLKBX Lab identity and public SDK surface.
- `ActionEvidenceBundle`, `GateAnalysisResult`, `InkReceiptResult`, and `ReceiptComparisonPacket` objects.
- `blkbx-lab` CLI with `demo`, `doctor`, `trace`, `analyze`, `gate`, `verify`, `tamper`, `explain`, `report`, and `compare` commands.
- Qwen3.5 claims demo (`qwen35-claims`).
- Thin-waist adapter layer for model integration.
- Ink Receipt core with canonical hashing, dev signing, and verification.
- Gate policy engine with `action-gate`, `decision-gate`, `trace-only`, and `human-review-required` policies.
- JSON schemas for `ink_manifest.v1`, `ink_receipt.v1`, `gate_decision.v1`, and `receipt_comparison.v1`.

### Changed
- Renamed `mech_lab` package to `blkbx_lab`.
- Renamed `mechlab` CLI to `blkbx-lab`.
- Moved mechanistic interpretability material (`internal/blt` and `internal/mair`) behind a legacy boundary.
- Updated `pyproject.toml` metadata to reflect the new accountable AI focus.

### Deprecated
- `mech_lab` package (use `blkbx_lab` instead).
- `mechlab` CLI (use `blkbx-lab` instead).
