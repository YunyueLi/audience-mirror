"""Codex CLI visual-frame baseline for governed multimodal Timeline extraction.

This adapter deliberately does not claim native video or audio understanding. It
attaches a bounded set of timestamped local evidence frames to an ephemeral
Codex CLI call, then emits the same provider-independent analysis contract used
by the native-video adapter.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Any

from .base import ModelUsage, VideoAnalysisRequest, VideoAnalysisResult
from .gemini import SYSTEM_TASK, VIDEO_ANALYSIS_SCHEMA, _parse_json_text


FRAME_BASELINE_TASK = """你收到的是按时间排序的离散证据帧，不是完整视频，也没有音轨。
只报告画面中实际可见的角色、物体、动作状态、构图和画面文字；不要声称听到了对白、音乐或声音。
相邻证据帧之间发生的过程属于不确定推断，必须写入 uncertainties。
segments 仍需覆盖 0 到视频时长，但边界只能视为基于抽帧的近似时间窗。
不要使用片名、网页标题或外部知识补齐画面。"""


class CodexFrameVideoProvider:
    """Bounded fixed-frame visual baseline backed by an authenticated Codex CLI."""

    provider_name = "openai-codex-cli-frame-baseline"

    def __init__(
        self,
        model_id: str = "gpt-5.6-sol",
        *,
        effort: str = "xhigh",
        executable: str = "codex",
        max_images: int = 12,
        timeout_seconds: int = 420,
    ) -> None:
        if not 2 <= max_images <= 16:
            raise ValueError("max_images must be between 2 and 16")
        self.model_id = model_id
        self.effort = effort
        self.executable = executable
        self.max_images = max_images
        self.timeout_seconds = timeout_seconds

    def _selected_frames(self, request: VideoAnalysisRequest) -> list[dict[str, Any]]:
        raw_frames = request.extensions.get("frame_evidence", [])
        if not isinstance(raw_frames, list):
            raise ValueError("frame_evidence must be a list")
        frames: list[dict[str, Any]] = []
        for item in raw_frames:
            if not isinstance(item, dict):
                continue
            path = Path(str(item.get("path") or "")).expanduser().resolve()
            timestamp_ms = item.get("t_ms")
            if path.is_file() and isinstance(timestamp_ms, int) and timestamp_ms >= 0:
                frames.append({"path": path, "t_ms": timestamp_ms})
        frames.sort(key=lambda item: (item["t_ms"], str(item["path"])))
        if len(frames) < 2:
            raise ValueError("Codex frame baseline requires at least two timestamped evidence frames")
        if len(frames) <= self.max_images:
            return frames
        # Scene-change sampling is intentionally dense around cuts and sparse in
        # long steady passages. Selecting by frame index would therefore spend
        # most of the model budget on high-cut regions and leave large temporal
        # blind spots. Pick the nearest evidence frame to evenly spaced time
        # targets instead, preserving endpoints and full-duration coverage.
        selected_indices: set[int] = set()
        for index in range(self.max_images):
            target_ms = round(index * request.duration_ms / (self.max_images - 1))
            nearest_index = min(
                range(len(frames)),
                key=lambda frame_index: (abs(frames[frame_index]["t_ms"] - target_ms), frame_index),
            )
            selected_indices.add(nearest_index)
        return [frames[index] for index in sorted(selected_indices)]

    def analyze(self, request: VideoAnalysisRequest) -> VideoAnalysisResult:
        if not request.allow_remote_processing:
            raise PermissionError("allow_remote_processing=false；未将证据帧发送到第三方模型。")
        if request.data_classification not in {"public", "internal"}:
            raise PermissionError(
                "Codex CLI 公有模型路由默认拒绝 confidential/restricted 素材；请改用经确认的私有部署路由。"
            )
        frames = self._selected_frames(request)
        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="audience-mirror-codex-frames-") as temporary_directory:
            temporary = Path(temporary_directory)
            schema_path = temporary / "response.schema.json"
            output_path = temporary / "response.json"
            schema_path.write_text(
                json.dumps(VIDEO_ANALYSIS_SCHEMA, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            image_paths: list[Path] = []
            frame_lines: list[str] = []
            for index, frame in enumerate(frames, start=1):
                suffix = frame["path"].suffix.lower() if frame["path"].suffix else ".jpg"
                target = temporary / f"frame-{index:02d}{suffix}"
                shutil.copyfile(frame["path"], target)
                image_paths.append(target)
                frame_lines.append(f"图像 {index:02d}：{frame['t_ms']} ms")
            frame_contract = SYSTEM_TASK.replace("完整观看输入视频", "分析按时间排序的离散证据帧")
            prompt = (
                f"{frame_contract}\n\n{FRAME_BASELINE_TASK}\n\n"
                f"视频时长：{request.duration_ms} ms。输出语言：{request.language}。\n"
                f"附件与时间戳映射：\n" + "\n".join(frame_lines)
            )
            if request.task_prompt:
                prompt += f"\n任务补充：{request.task_prompt}"
            command = [
                self.executable,
                "exec",
                "--cd",
                str(temporary),
                "--skip-git-repo-check",
                "--ephemeral",
                "--ignore-rules",
                "--sandbox",
                "read-only",
                "--image",
                *[str(path) for path in image_paths],
                "--model",
                self.model_id,
                "--config",
                f'model_reasoning_effort="{self.effort}"',
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(output_path),
                prompt,
            ]
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
            if process.returncode != 0:
                error = (process.stderr or process.stdout).strip()
                raise RuntimeError(f"Codex CLI frame analysis failed ({process.returncode}): {error[-1200:]}")
            if not output_path.is_file():
                raise ValueError("Codex CLI did not write the structured video analysis")
            analysis = _parse_json_text(output_path.read_text(encoding="utf-8"))
        return VideoAnalysisResult(
            provider=self.provider_name,
            model_id=self.model_id,
            analysis=analysis,
            usage=ModelUsage(latency_ms=latency_ms),
            warnings=(
                f"固定抽帧视觉基线仅发送 {len(frames)} 张证据帧；未发送原视频或音轨。",
                "选帧策略为 temporal_stratified_nearest；时间点（ms）："
                + ",".join(str(frame["t_ms"]) for frame in frames),
                "帧间动作、对白、音乐与声音均未被直接观察，不能等同于原生完整视频理解。",
            ),
        )
