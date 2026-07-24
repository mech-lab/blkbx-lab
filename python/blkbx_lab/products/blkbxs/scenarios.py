"""Seeded BLKBXS UBR demo scenarios."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any

from .._common import clone
from .graph import validate_graph


def smb_loan_demo_fixture() -> dict[str, Any]:
    """Load the committed SMB loan fixture generated from the UBR demo bundle."""
    return json.loads(files("blkbx_lab.products.blkbxs.fixtures").joinpath("smb_loan_demo.json").read_text(encoding="utf-8"))


def smb_loan_demo() -> dict[str, Any]:
    fixture = smb_loan_demo_fixture()
    validation = validate_graph(
        fixture["receipts"],
        evidence_manifest=fixture["evidence_manifest"],
        verifier_report=fixture["verifier_report"],
    )
    ordered_receipts = _ordered_receipts(fixture["receipts"], validation["topological_order"])
    demo = clone(fixture)
    demo["receipts"] = ordered_receipts
    demo["graph_validation"] = validation
    return demo


def _ordered_receipts(receipts: list[dict[str, Any]], order: list[str]) -> list[dict[str, Any]]:
    by_id = {receipt.get("id"): receipt for receipt in receipts}
    ordered = [by_id[receipt_id] for receipt_id in order if receipt_id in by_id]
    return [*ordered, *[receipt for receipt in receipts if receipt.get("id") not in set(order)]]


__all__ = ["smb_loan_demo", "smb_loan_demo_fixture"]
