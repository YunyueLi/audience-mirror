"""Locate packaged read-only assets and the writable local workspace."""

from __future__ import annotations

import os
from pathlib import Path
import sys


SOURCE_CHECKOUT_ROOT = Path(__file__).resolve().parents[2]
INSTALLED_DATA_ROOT = Path(sys.prefix).resolve() / "share" / "audience-mirror"


def resource_root() -> Path:
    """Return the source checkout or wheel-installed runtime data root."""

    candidates = (
        SOURCE_CHECKOUT_ROOT,
        INSTALLED_DATA_ROOT,
        Path.cwd().resolve(),
    )
    for candidate in candidates:
        if (candidate / "schemas" / "timeline.schema.json").is_file():
            return candidate
    raise RuntimeError(
        "Audience Mirror 运行时资源缺失；请从源码根目录运行，或重新安装完整 wheel。"
    )


def workspace_root() -> Path:
    """Return a writable workspace without writing into installed package data."""

    configured = os.environ.get("AUDIENCE_MIRROR_WORKSPACE")
    if configured:
        return Path(configured).expanduser().resolve()
    if (SOURCE_CHECKOUT_ROOT / "pyproject.toml").is_file():
        return SOURCE_CHECKOUT_ROOT
    return Path.cwd().resolve()


def resource_path(*parts: str) -> Path:
    return resource_root().joinpath(*parts)
