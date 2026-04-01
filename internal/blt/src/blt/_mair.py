from __future__ import annotations

def ensure_mair_importable() -> None:
    try:
        import mair  # noqa: F401
        return
    except Exception as exc:  # pragma: no cover - exercised in integration usage
        raise ImportError(
            "Unable to import mair. Install it editable with "
            "python -m pip install -e '/Volumes/128/MAIR[dev]'"
        ) from exc
