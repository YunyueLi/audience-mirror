"""Gemini Files API adapter for native audio-visual video understanding."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from .base import ModelUsage, VideoAnalysisRequest, VideoAnalysisResult


SYSTEM_TASK = """你是 Audience Mirror 的视频事实层提取器。完整观看输入视频，输出严格 JSON。
只描述画面、对白、声音、音乐、文字、角色行为和叙事事件；不要模拟观众反应，不要预测市场结果。
时间必须是整数毫秒，并以输入视频起点为 0。无法确认的事实写入 uncertainties。
输出结构：
{
  "summary": "全片事实摘要",
  "segments": [
    {
      "t_start_ms": 0,
      "t_end_ms": 1000,
      "label": "简短标签",
      "summary": "该段发生的事实",
      "observations": [
        {"modality": "visual|speech|text|music|sound|multimodal", "kind": "类型", "text": "事实", "confidence": 0.0}
      ],
      "entity_refs": ["匿名实体标识"],
      "salience_tags": ["exposition|character_change|relationship_change|goal_change|reveal|conflict|payoff|visual_spectacle|music_change|silence|ui_change|purchase_exposure|share_hook|safety_critical"],
      "uncertainties": ["不确定点"]
    }
  ],
  "uncertainties": ["全局不确定点"]
}
segments 必须按时间排序、不得越界、不得包含片名外部知识。"""

VIDEO_ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "segments", "uncertainties"],
    "properties": {
        "summary": {"type": "string"},
        "segments": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "t_start_ms",
                    "t_end_ms",
                    "label",
                    "summary",
                    "observations",
                    "entity_refs",
                    "salience_tags",
                    "uncertainties",
                ],
                "properties": {
                    "t_start_ms": {"type": "integer", "minimum": 0},
                    "t_end_ms": {"type": "integer", "minimum": 1},
                    "label": {"type": "string"},
                    "summary": {"type": "string"},
                    "observations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["modality", "kind", "text", "confidence"],
                            "properties": {
                                "modality": {
                                    "enum": ["visual", "speech", "text", "music", "sound", "multimodal"]
                                },
                                "kind": {"type": "string"},
                                "text": {"type": "string"},
                                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            },
                        },
                    },
                    "entity_refs": {"type": "array", "items": {"type": "string"}},
                    "salience_tags": {"type": "array", "items": {"type": "string"}},
                    "uncertainties": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "uncertainties": {"type": "array", "items": {"type": "string"}},
    },
}


def _parse_json_text(text: str) -> dict[str, Any]:
    value = text.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        value = "\n".join(lines)
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("video model response must be a JSON object")
    if not isinstance(parsed.get("segments"), list):
        raise ValueError("video model response must contain a segments array")
    return parsed


class GeminiVideoProvider:
    """Native full-video adapter. Remote processing must be explicitly allowed."""

    provider_name = "google-gemini-files-api"

    def __init__(
        self,
        model_id: str = "gemini-3.7-flash",
        *,
        api_key: str | None = None,
        poll_interval_seconds: float = 2.0,
        activation_timeout_seconds: float = 300.0,
        delete_remote_file: bool = True,
    ) -> None:
        self.model_id = model_id
        self._api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.poll_interval_seconds = poll_interval_seconds
        self.activation_timeout_seconds = activation_timeout_seconds
        self.delete_remote_file = delete_remote_file

    def _client(self) -> tuple[Any, Any]:
        if not self._api_key:
            raise RuntimeError("缺少 GEMINI_API_KEY 或 GOOGLE_API_KEY，未执行远程视频上传。")
        try:
            from google import genai  # type: ignore[import-not-found]
            from google.genai import types  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "Gemini 视频调用需要 gemini extra：python -m pip install -e '.[gemini]'"
            ) from exc
        return genai.Client(api_key=self._api_key), types

    def analyze(self, request: VideoAnalysisRequest) -> VideoAnalysisResult:
        if not request.allow_remote_processing:
            raise PermissionError("allow_remote_processing=false；未将视频发送到第三方模型。")
        if request.data_classification not in {"public", "internal"}:
            raise PermissionError(
                "Gemini 公有 API Adapter 默认拒绝 confidential/restricted 素材；请改用经确认的私有部署路由。"
            )
        video_path = Path(request.video_path).expanduser().resolve()
        if not video_path.is_file():
            raise FileNotFoundError(video_path)
        client, types = self._client()
        started = time.perf_counter()
        uploaded = None
        warnings: list[str] = []
        try:
            uploaded = client.files.upload(file=str(video_path))
            deadline = time.monotonic() + self.activation_timeout_seconds
            while getattr(getattr(uploaded, "state", None), "name", None) == "PROCESSING":
                if time.monotonic() >= deadline:
                    raise TimeoutError("Gemini video file did not become ACTIVE before timeout")
                time.sleep(self.poll_interval_seconds)
                uploaded = client.files.get(name=uploaded.name)
            state_name = getattr(getattr(uploaded, "state", None), "name", None)
            if state_name not in {None, "ACTIVE"}:
                raise RuntimeError(f"Gemini file processing failed with state {state_name!r}")

            task = request.task_prompt or "按上述合同提取完整视频的证据时间线。"
            prompt = (
                f"{SYSTEM_TASK}\n\n视频时长上限：{request.duration_ms} ms。"
                f"\n输出语言：{request.language}。\n任务补充：{task}"
            )
            # generateContent remains supported by Gemini 3.7 and is the stable
            # google-genai surface; the SDK currently labels Interactions as experimental.
            response = client.models.generate_content(
                model=self.model_id,
                contents=[uploaded, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=VIDEO_ANALYSIS_SCHEMA,
                ),
            )
            response_text = getattr(response, "text", "") or ""
            usage_metadata = getattr(response, "usage_metadata", None)
            analysis = _parse_json_text(response_text)
            usage = ModelUsage(
                input_tokens=(
                    getattr(usage_metadata, "input_tokens", None)
                    or getattr(usage_metadata, "prompt_token_count", None)
                ),
                output_tokens=(
                    getattr(usage_metadata, "output_tokens", None)
                    or getattr(usage_metadata, "candidates_token_count", None)
                ),
                media_tokens=None,
                latency_ms=int((time.perf_counter() - started) * 1000),
                estimated_cost_usd=None,
            )
            if request.fps_hint is not None:
                warnings.append(
                    "当前 Files API 适配器记录了 fps_hint，但未强制覆盖服务端采样；快动作需用局部高帧率复核器。"
                )
            request_id = getattr(response, "response_id", None)
        finally:
            if uploaded is not None and self.delete_remote_file:
                try:
                    client.files.delete(name=uploaded.name)
                except Exception:
                    # The result must disclose failed cleanup without exposing remote identifiers.
                    warnings.append("Gemini 临时文件自动删除未确认；请查看供应商控制台的保留状态。")
        return VideoAnalysisResult(
            provider=self.provider_name,
            model_id=self.model_id,
            analysis=analysis,
            usage=usage,
            provider_request_id=request_id,
            warnings=tuple(warnings),
        )
