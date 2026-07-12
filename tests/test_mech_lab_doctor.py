from __future__ import annotations

import importlib
import sys
import warnings

import pytest

import blkbx_lab as bl
from blkbx_lab.objects import DoctorResult


def test_doctor_public_contract():
    result = bl.doctor()

    assert isinstance(result, DoctorResult)
    assert result.status == "ready"
    assert result.demo_ready is True
    assert result.real_replay_ready is False
    assert "BLKBX Lab Doctor" in result.report


def test_mech_lab_package_is_a_deprecated_shim():
    sys.modules.pop("mech_lab", None)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        shim = importlib.import_module("mech_lab")

    assert any("deprecated" in str(w.message).lower() for w in caught)
    assert shim.demo is bl.demo
    assert shim.verify is bl.verify


def test_mechlab_cli_shim_warns_and_delegates(monkeypatch):
    import mech_lab.cli as shim_cli

    monkeypatch.setattr(shim_cli, "blkbx_main", lambda: 0)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(SystemExit) as excinfo:
            shim_cli.main()

    assert excinfo.value.code == 0
    assert any("deprecated" in str(w.message).lower() for w in caught)
