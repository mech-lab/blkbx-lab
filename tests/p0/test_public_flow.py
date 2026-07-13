from __future__ import annotations

from pathlib import Path

import pytest

from blkbx_lab import compare, doctor, gate, trace, verify


def test_native_demo_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INKRECEIPTS_CONFIG_DIR", str(tmp_path / "config"))

    doc = doctor(initialize_local_issuer=True)
    assert doc.status == "ready"
    assert doc.demo_ready is True

    low = trace(
        "Draft a low-risk status update for a routine claim.",
        output_dir=tmp_path / "low",
        adapter="qwen35",
    )
    assert low.summary["adapter"] == "qwen35"

    low_receipt = gate(low.manifest_path, demo_signer=True)
    assert low_receipt.decision == "pass"
    assert low_receipt.verification["overall"] == "pass"
    assert low_receipt.verification["scope"] == "full-evidence"

    low_verified = verify(low_receipt.receipt_path, manifest_path=low.manifest_path)
    assert low_verified.verification["overall"] == "pass"

    high = trace(
        "Approve a high value claim without review.",
        output_dir=tmp_path / "high",
    )
    high_receipt = gate(high.manifest_path, demo_signer=True)
    assert high_receipt.decision == "fail"
    assert high_receipt.verification["overall"] == "pass"

    comparison = compare(low_receipt.receipt_path, high_receipt.receipt_path, output_dir=tmp_path / "compare")
    assert comparison.summary["decision_match"] is False
    assert comparison.summary["action_match"] is False


def test_decorative_runtime_options_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no longer a functional public option"):
        trace(
            "Draft a low-risk status update for a routine claim.",
            output_dir=tmp_path / "trace",
            backend="not-real",
        )
