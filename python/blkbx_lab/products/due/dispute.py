"""DUE dispute-readiness export."""

from __future__ import annotations

from . import bundle


def export(
    receipt: dict,
    bundle_type: str = "dispute_readiness_bundle",
    audience: str = "counsel",
    notes: str | None = None,
) -> dict:
    return bundle.export(
        receipt,
        bundle_type=bundle_type,
        audience=audience,
        notes=notes,
        bundle_sections=[
            "Matter Context",
            "Authority",
            "Privilege",
            "Disclosure",
            "Human Review",
            "Dispute Readiness",
        ],
    )


__all__ = ["export"]
