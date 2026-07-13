"""Optional lazy shim around the blkbx_lab._ink_native extension module."""

from __future__ import annotations

import importlib
import importlib.util
from types import ModuleType

MISSING_RUST_MESSAGE = "receipt-core rust extension is not installed"
_REQUIRED_EXPORTS = {"sha256_bytes", "public_key_from_seed", "sign_digest", "verify_digest"}

_MODULE: ModuleType | None = None


def available() -> bool:
    if importlib.util.find_spec("blkbx_lab._ink_native") is None:
        return False
    try:
        module = importlib.import_module("blkbx_lab._ink_native")
    except ImportError:
        return False
    return all(hasattr(module, name) for name in _REQUIRED_EXPORTS)


def _load_module() -> ModuleType:
    global _MODULE
    if _MODULE is not None:
        return _MODULE
    try:
        _MODULE = importlib.import_module("blkbx_lab._ink_native")
    except ImportError as exc:
        raise RuntimeError(MISSING_RUST_MESSAGE) from exc
    return _MODULE


def sha256_bytes(data: bytes) -> bytes:
    return bytes(_load_module().sha256_bytes(data))


def public_key_from_seed(seed: bytes) -> bytes:
    return bytes(_load_module().public_key_from_seed(seed))


def sign_digest(digest: bytes, seed: bytes) -> bytes:
    return bytes(_load_module().sign_digest(digest, seed))


def verify_digest(digest: bytes, public_key: bytes, signature: bytes) -> bool:
    return bool(_load_module().verify_digest(digest, public_key, signature))
