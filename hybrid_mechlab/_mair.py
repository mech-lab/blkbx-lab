from __future__ import annotations


def ensure_mair_importable() -> None:
    try:
        import mair  # noqa: F401
        return
    except Exception as exc:  # pragma: no cover - exercised in integration usage
        raise ImportError(
            "Unable to import mair. Install the unified blkbx-lab repo dependencies "
            "or ensure internal/ink/legacy_mair/src is on PYTHONPATH"
        ) from exc
