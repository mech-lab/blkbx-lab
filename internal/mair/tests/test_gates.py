from __future__ import annotations

import json
from pathlib import Path

from mair.gates import run_gates, write_receipt
from mair.manifest import write_manifest
from mair.validate import validate_artifact

from tests.support import write_full_artifact_set


def test_run_gates_passes_when_thresholds_are_satisfied(tmp_path: Path) -> None:
    write_full_artifact_set(tmp_path)
    manifest_path = write_manifest(tmp_path, trace_id="trace-1", producer="mair:test:0.1.0")

    receipt = run_gates(
        manifest_path,
        profile={
            "required_artifacts": ["topology_summary", "grouped_clt_bundle", "offline_topology_report"],
            "max_bridge_dependence": 0.5,
            "max_gluing_defect": 0.5,
        },
    )

    assert receipt["decision"] == "pass"
    assert receipt["summary"]["failed"] == []
    assert receipt["gates"]["bridge_dependence_within_threshold"] is True
    assert receipt["gates"]["gluing_defect_within_threshold"] is True


def test_write_receipt_emits_valid_assurance_artifact(tmp_path: Path) -> None:
    write_full_artifact_set(tmp_path)
    manifest_path = write_manifest(tmp_path, trace_id="trace-1", producer="mair:test:0.1.0")

    receipt_path = write_receipt(
        manifest_path,
        profile={"max_bridge_dependence": 0.2, "max_gluing_defect": 0.1},
    )

    validate_artifact(receipt_path, "assurance_receipt")
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["decision"] == "fail"
    assert "bridge_dependence_within_threshold" in payload["summary"]["failed"]
    assert "gluing_defect_within_threshold" in payload["summary"]["failed"]
