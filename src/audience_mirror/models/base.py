"""Model-independent contracts for native video understanding providers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ModelUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None
    media_tokens: int | None = None
    latency_ms: int | None = None
    estimated_cost_usd: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "media_tokens": self.media_tokens,
            "latency_ms": self.latency_ms,
            "estimated_cost_usd": self.estimated_cost_usd,
        }


@dataclass(frozen=True, slots=True)
class VideoAnalysisRequest:
    video_path: Path
    asset_hash: str
    duration_ms: int
    language: str = "zh-CN"
    task_prompt: str | None = None
    fps_hint: float | None = None
    data_classification: str = "public"
    allow_remote_processing: bool = False
    extensions: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class VideoAnalysisResult:
    provider: str
    model_id: str
    analysis: dict[str, Any]
    usage: ModelUsage
    provider_request_id: str | None = None
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model_id": self.model_id,
            "analysis": self.analysis,
            "usage": self.usage.to_dict(),
            "provider_request_id": self.provider_request_id,
            "warnings": list(self.warnings),
        }


class VideoModelProvider(Protocol):
    provider_name: str
    model_id: str

    def analyze(self, request: VideoAnalysisRequest) -> VideoAnalysisResult: ...
