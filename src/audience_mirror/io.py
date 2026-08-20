"""Safe local JSON and text artifact helpers."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from .hashing import sha256_text


def read_json(path: str | Path) -> Any:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str | Path, value: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_text(path: str | Path, value: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(value, encoding="utf-8")


def file_sha256(path: str | Path) -> str:
    return sha256_text(Path(path).read_text(encoding="utf-8"))


def binary_file_sha256(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Hash a binary artifact without loading it into memory."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()
