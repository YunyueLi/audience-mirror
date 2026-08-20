"""Build the redistributable, read-only browser demo bundle.

The bundle contains only the repository's synthetic fixture and deterministic
runtime output. It deliberately exposes no upload, model, or calibration
capability so a static deployment cannot imply that a backend mutation ran.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .__init__ import __version__
from .webapp import _demo_record, _public_record


STATIC_DEMO_SCHEMA_VERSION = "audience-mirror.static-demo/v0.1"


def build_static_demo_bundle() -> dict[str, Any]:
    """Return the deterministic public fixture and an honest capability ledger."""

    experiment = _public_record(_demo_record())
    static_limitations = [
        "公开体验版为只读静态部署，不会上传、解析或发送你输入的链接。",
        "页面展示的是仓库内合成 Fixture 与确定性工程基线，不是在线模型运行。",
        "完整链接导入、真实视频解析、模型顺序体验与真人校准需要在本机工作台运行。",
    ]
    experiment["limitations"] = [*experiment["limitations"], *static_limitations]
    return {
        "schema_version": STATIC_DEMO_SCHEMA_VERSION,
        "health": {
            "ok": True,
            "version": __version__,
            "deployment_mode": "static_public_demo",
            "capabilities": {
                "static_public_demo": True,
                "environment_contract": True,
                "local_video_decode": False,
                "direct_video_url": False,
                "platform_video_url": False,
                "gemini_native_video": False,
                "codex_frame_analysis": False,
                "claude_code_cli": False,
                "codex_cli": False,
                "human_calibration": False,
            },
            "privacy": {
                "remote_processing_default": False,
                "network_processing": False,
                "bundled_data": "synthetic_fixture_only",
                "human_records": 0,
            },
        },
        "experiment_index": {
            "experiments": [],
            "count": 0,
            "persistence": "read_only_static_fixture",
        },
        "experiment": experiment,
        "limitations": static_limitations,
    }


def export_static_demo(path: str | Path) -> Path:
    """Write a browser-loadable bundle without private paths or runtime data."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        build_static_demo_bundle(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    destination.write_text(
        "/* Generated from the public synthetic fixture. Do not edit by hand. */\n"
        f"window.__AUDIENCE_MIRROR_STATIC_DEMO__={payload};\n",
        encoding="utf-8",
    )
    return destination
