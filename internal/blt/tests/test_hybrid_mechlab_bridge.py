from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("blt")
pytest.importorskip("mair.validate")

from blt.export import export_hybrid_mechlab_trace, run_trace
from blt.integrations.hybrid_mechlab import TRACE_SCHEMA_KEYS, build_hybrid_mechlab_record


def test_build_hybrid_mechlab_record_from_manifest(tmp_path: Path) -> None:
    manifest_path = run_trace("Bridge tract export test.", "trace-blt-hm-1", tmp_path, backend="mock")
    record = build_hybrid_mechlab_record(manifest_path)
    assert tuple(record.keys()) == TRACE_SCHEMA_KEYS
    assert record["trace_id"] == "trace-blt-hm-1"
    assert record["family"] == "qwen3.5-hybrid"
    assert record["backend"] == "mock"
    assert "codes" in record["capture"]
    assert record["sparse_codes"]


def test_export_hybrid_mechlab_trace_writes_json(tmp_path: Path) -> None:
    manifest_path = run_trace("Export the hm trace.", "trace-blt-hm-2", tmp_path, backend="mock")
    output_path = export_hybrid_mechlab_trace(manifest_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert output_path.name == "trace-blt-hm-2.hybrid_mechlab_trace.json"
    assert payload["trace_id"] == "trace-blt-hm-2"
    assert payload["transport_digest"]["local_steps"] > 0
