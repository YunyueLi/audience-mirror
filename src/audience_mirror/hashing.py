"""Deterministic hashing helpers used by experiment manifests and event streams."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Return a stable JSON representation suitable for fingerprints."""

    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fingerprint(value: Any) -> str:
    return sha256_text(canonical_json(value))


def event_fingerprint(event: dict[str, Any]) -> str:
    """Hash a Trace Event while excluding its self-referential event_hash."""

    material = {key: value for key, value in event.items() if key != "event_hash"}
    return fingerprint(material)
