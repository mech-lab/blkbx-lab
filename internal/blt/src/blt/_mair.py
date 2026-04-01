from __future__ import annotations

def ensure_mair_importable() -> None:
    try:
        import mair  # noqa: F401
        return
    except Exception as exc:  # pragma: no cover - exercised in integration usage
        raise ImportError(
            "Unable to import mair. Install the unified mech-lab repo dependencies "
            "or ensure internal/mair/src is on PYTHONPATH"
        ) from exc
