from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from mair.manifest import build_manifest, write_manifest


def _write_sample_run(root: Path) -> None:
    (root / "mair_graph_ir.v1.json").write_text(json.dumps({"trace_id": "t1", "model_family": "qwen", "model_variant": "mock", "nodes": [], "edges": []}), encoding="utf-8")
    table = pa.table(
        {
            "trace_id": ["t1"],
            "token_index": [0],
            "block_id": ["block-0"],
            "code_group": ["g0"],
            "reconstruction_error": [0.1],
            "bridge_strength": [0.2],
        }
    )
    pq.write_table(table, root / "blt_codes.v1.parquet")


def test_build_manifest_collects_known_artifacts(tmp_path: Path) -> None:
    _write_sample_run(tmp_path)
    manifest = build_manifest(tmp_path, trace_id="t1", producer="mair:test:0.1.0")
    names = {artifact.artifact_type for artifact in manifest.artifacts}
    assert names == {"mair_graph_ir", "blt_codes"}


def test_write_manifest_writes_json(tmp_path: Path) -> None:
    _write_sample_run(tmp_path)
    path = write_manifest(tmp_path, trace_id="t1", producer="mair:test:0.1.0")
    assert path.name == "mair_manifest.v1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["trace_id"] == "t1"
