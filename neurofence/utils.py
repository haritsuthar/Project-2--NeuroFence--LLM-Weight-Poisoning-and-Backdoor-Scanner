"""
Shared utility helpers for NeuroFence.
Compatible with Python 3.13.
"""

import hashlib
import json
import logging
import os
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# File utilities
# ------------------------------------------------------------------

def sha256_file(path: str) -> str:
    """Return the SHA-256 hex digest of a file, or 'n/a' if missing/unreadable."""
    if not os.path.exists(path):
        return "n/a"
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError as exc:
        logger.warning("sha256_file: cannot read %s — %s", path, exc)
        return "n/a"


def ensure_dir(path: str) -> None:
    """Create *path* (and any missing parents) if it does not already exist."""
    if path:
        os.makedirs(path, exist_ok=True)


def save_json(path: str, obj: Any) -> None:
    """Serialise *obj* to JSON at *path*, creating parent directories as needed."""
    ensure_dir(os.path.dirname(os.path.abspath(path)))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, default=_json_default)


def load_json(path: str, default: Optional[Any] = None) -> Any:
    """Load JSON from *path*; return *default* (empty dict) on any failure."""
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("load_json: failed to read %s — %s", path, exc)
        return default


# ------------------------------------------------------------------
# Numeric helpers
# ------------------------------------------------------------------

def activation_energy(arr: Any) -> float:
    """Mean squared value of *arr* (L2 energy proxy)."""
    x = np.asarray(arr, dtype=np.float64)
    return float(np.mean(x * x))


# ------------------------------------------------------------------
# Internal
# ------------------------------------------------------------------

def _json_default(obj: Any) -> Any:
    """Make numpy scalars / arrays JSON-serialisable."""
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj).__name__!r} is not JSON serialisable")
