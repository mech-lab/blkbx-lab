from __future__ import annotations

import blkbx_lab as bl
from blkbx_lab.objects import DoctorResult


def test_doctor_public_contract():
    result = bl.doctor()

    assert isinstance(result, DoctorResult)
    assert result.status == "ready"
    assert isinstance(result.demo_ready, bool)
    assert isinstance(result.real_replay_ready, bool)
    assert "BLKBX Lab Doctor" in result.report
