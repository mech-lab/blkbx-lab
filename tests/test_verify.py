from __future__ import annotations

import json
from pathlib import Path

import blkbx_lab as bl


def _receipt_path(tmp_path: Path) -> Path:
    result = bl.demo(output_dir=tmp_path / "demo")
    return Path(result.receipt_path)


def test_verify_clean(tmp_path: Path) -> None:
    receipt_path = _receipt_path(tmp_path)
    result = bl.verify(receipt_path)
    assert result.verification["valid"] is True
    assert result.verification["overall"] == "pass"


def test_verify_tampered_decision(tmp_path: Path) -> None:
    receipt_path = _receipt_path(tmp_path)
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    payload["decision"] = "block"
    receipt_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result = bl.verify(receipt_path)
    assert result.verification["valid"] is False
    assert result.verification["overall"] == "fail"


def test_verify_tampered_policy(tmp_path: Path) -> None:
    receipt_path = _receipt_path(tmp_path)
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    payload["policy"]["id"] = "tampered-policy"
    receipt_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result = bl.verify(receipt_path)
    assert result.verification["valid"] is False
    assert result.verification["overall"] == "fail"


def test_verify_tampered_evidence(tmp_path: Path) -> None:
    receipt_path = _receipt_path(tmp_path)
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    payload["reason_codes"] = ["TAMPERED_PAYLOAD"]
    receipt_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result = bl.verify(receipt_path)
    assert result.verification["valid"] is False
    assert result.verification["overall"] == "fail"
