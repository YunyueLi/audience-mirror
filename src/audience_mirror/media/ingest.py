"""Local, evidence-preserving video ingestion using optional PyAV and Pillow.

The parser performs real container decoding. It does not pretend that sampled frames
are semantic understanding: its observations are explicitly labelled as local frame
samples until a multimodal provider adds model-derived observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import wave

from ..hashing import fingerprint
from ..io import binary_file_sha256, write_json
from ..validation import validate_timeline


@dataclass(frozen=True, slots=True)
class VideoIngestConfig:
    sample_interval_ms: int = 5_000
    scene_threshold: float = 0.24
    min_scene_gap_ms: int = 800
    max_frames: int = 240
    jpeg_quality: int = 88
    extract_audio: bool = True
    language: str = "und"
    data_classification: str = "public"
    export_policy: str = "authorized"
    retention_class: str = "prototype"
    rights_manifest_id: str = "rights-local-prototype"

    def __post_init__(self) -> None:
        if self.sample_interval_ms < 100:
            raise ValueError("sample_interval_ms must be at least 100")
        if not 0 <= self.scene_threshold <= 1:
            raise ValueError("scene_threshold must be between 0 and 1")
        if self.min_scene_gap_ms < 0 or self.max_frames <= 0:
            raise ValueError("min_scene_gap_ms must be non-negative and max_frames positive")
        if not 1 <= self.jpeg_quality <= 100:
            raise ValueError("jpeg_quality must be between 1 and 100")
        if self.data_classification not in {"public", "internal", "confidential", "restricted"}:
            raise ValueError("unsupported data_classification")
        if self.export_policy not in {"no_export", "redacted_only", "authorized"}:
            raise ValueError("unsupported export_policy")


@dataclass(frozen=True, slots=True)
class VideoIngestResult:
    timeline: dict[str, Any]
    manifest: dict[str, Any]
    output_directory: Path


def _imports() -> tuple[Any, Any, Any, Any]:
    try:
        import av  # type: ignore[import-not-found]
        from PIL import Image, ImageChops, ImageStat  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "真实视频解析需要 media extra：python -m pip install -e '.[media]'"
        ) from exc
    return av, Image, ImageChops, ImageStat


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _duration_ms(container: Any, stream: Any) -> int | None:
    if getattr(stream, "duration", None) is not None and getattr(stream, "time_base", None) is not None:
        return max(1, int(float(stream.duration * stream.time_base) * 1000))
    container_duration = getattr(container, "duration", None)
    if container_duration is not None:
        return max(1, int(container_duration / 1000))
    return None


def _frame_timestamp_ms(frame: Any, stream: Any, fallback_index: int) -> int:
    if getattr(frame, "time", None) is not None:
        return max(0, int(float(frame.time) * 1000))
    if frame.pts is not None and stream.time_base is not None:
        return max(0, int(float(frame.pts * stream.time_base) * 1000))
    rate = float(stream.average_rate) if stream.average_rate else 25.0
    return max(0, int(fallback_index / rate * 1000))


def _difference_ratio(current: Any, previous: Any, ImageChops: Any, ImageStat: Any) -> float:
    difference = ImageChops.difference(current, previous)
    mean = ImageStat.Stat(difference).mean
    return sum(mean) / (len(mean) * 255.0)


def _extract_audio(source: Path, target: Path, av: Any) -> dict[str, Any] | None:
    with av.open(str(source)) as container:
        streams = list(container.streams.audio)
        if not streams:
            return None
        stream = streams[0]
        resampler = av.AudioResampler(format="s16", layout="mono", rate=16_000)
        target.parent.mkdir(parents=True, exist_ok=True)
        written_frames = 0
        with wave.open(str(target), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16_000)
            for frame in container.decode(stream):
                converted = resampler.resample(frame)
                if converted is None:
                    continue
                converted_frames = converted if isinstance(converted, list) else [converted]
                for audio_frame in converted_frames:
                    wav_file.writeframes(bytes(audio_frame.planes[0]))
                    written_frames += int(audio_frame.samples)
            flushed = resampler.resample(None)
            if flushed:
                flushed_frames = flushed if isinstance(flushed, list) else [flushed]
                for audio_frame in flushed_frames:
                    wav_file.writeframes(bytes(audio_frame.planes[0]))
                    written_frames += int(audio_frame.samples)
        return {
            "artifact_ref": f"audio:{binary_file_sha256(target)[:16]}",
            "relative_path": target.name,
            "content_hash": binary_file_sha256(target),
            "sample_rate": 16_000,
            "channels": 1,
            "duration_ms": int(written_frames / 16_000 * 1000),
        }


def _build_timeline(
    *,
    asset_hash: str,
    source_name: str,
    duration_ms: int,
    frames: list[dict[str, Any]],
    config: VideoIngestConfig,
    generated_at: str,
    container_metadata: dict[str, Any],
) -> dict[str, Any]:
    extractor_run_id = f"extract-local-video-{asset_hash[:12]}"
    asset_ref = f"asset:{asset_hash[:20]}"
    nodes: list[dict[str, Any]] = [
        {
            "node_id": "act-001",
            "parent_node_id": None,
            "level": "act",
            "t_start_ms": 0,
            "t_end_ms": duration_ms,
            "label": "完整素材",
            "summary": "本地解析生成的完整视频范围；尚未经过语义模型解释。",
            "observations": [],
            "entity_refs": [],
            "salience_tags": [],
            "review_status": "auto_checked",
            "review_notes": None,
            "extensions": {"source_name": source_name},
        }
    ]
    for index, frame in enumerate(frames):
        start_ms = 0 if index == 0 else int(frame["timestamp_ms"])
        if index + 1 < len(frames):
            end_ms = max(start_ms + 1, int(frames[index + 1]["timestamp_ms"]))
        else:
            end_ms = duration_ms
        if end_ms <= start_ms:
            end_ms = min(duration_ms, start_ms + 1)
        if end_ms <= start_ms:
            start_ms = max(0, duration_ms - 1)
            end_ms = duration_ms
        node_id = f"event-{index + 1:04d}"
        observation_id = f"observation-{index + 1:04d}-local-frame"
        nodes.append(
            {
                "node_id": node_id,
                "parent_node_id": "act-001",
                "level": "event",
                "t_start_ms": start_ms,
                "t_end_ms": end_ms,
                "label": f"本地采样段 {index + 1}",
                "summary": "真实解码帧的时间片；等待多模态模型或人工补充语义。",
                "observations": [
                    {
                        "observation_id": observation_id,
                        "modality": "visual",
                        "kind": "decoded_frame_sample",
                        "text": f"在 {frame['timestamp_ms']} ms 解码并保存一帧；不含语义判断。",
                        "epistemic_status": "observed",
                        "confidence": 1.0,
                        "evidence_refs": [
                            {
                                "ref_id": f"evidence-frame-{index + 1:04d}",
                                "evidence_type": "frame",
                                "t_start_ms": int(frame["timestamp_ms"]),
                                "t_end_ms": int(frame["timestamp_ms"]),
                                "object_ref": frame["artifact_ref"],
                                "hash_algorithm": "sha256",
                                "content_hash": frame["content_hash"],
                                "data_classification": config.data_classification,
                                "export_policy": config.export_policy,
                                "redaction_status": "not_required",
                                "excerpt": None,
                            }
                        ],
                        "producer_ref": extractor_run_id,
                    }
                ],
                "entity_refs": [],
                "salience_tags": [],
                "review_status": "auto_checked",
                "review_notes": "仅确认解码与时间戳；语义尚未人工确认。",
                "extensions": {
                    "sample_reason": frame["sample_reason"],
                    "source_timestamp_ms": frame["timestamp_ms"],
                },
            }
        )
    timeline = {
        "schema_version": "audience-mirror.timeline/v0.1",
        "timeline_id": f"timeline-{asset_hash[:16]}",
        "asset": {
            "asset_id": f"asset-{asset_hash[:16]}",
            "variant_id": "variant-a",
            "content_hash": asset_hash,
            "object_ref": asset_ref,
            "rights_manifest_id": config.rights_manifest_id,
        },
        "data_handling": {
            "data_classification": config.data_classification,
            "export_policy": config.export_policy,
            "retention_class": config.retention_class,
            "contains_personal_data": False,
            "redaction_status": "not_required",
        },
        "generated_at": generated_at,
        "frozen_at": None,
        "language": config.language,
        "duration_ms": duration_ms,
        "extractor_manifest": [
            {
                "extractor_run_id": extractor_run_id,
                "capability": "shot_detection",
                "producer": "audience-mirror.local-pyav-ingest",
                "model_id": None,
                "version": "0.1.0",
                "config_hash": fingerprint(config.__dict__ if hasattr(config, "__dict__") else {
                    field_name: getattr(config, field_name)
                    for field_name in config.__dataclass_fields__
                }),
                "ran_at": generated_at,
            }
        ],
        "nodes": nodes,
        "version_alignment": [],
        "review_summary": {
            "reviewed_node_count": 0,
            "corrected_node_count": 0,
            "disputed_node_count": 0,
            "reviewer_ref": None,
        },
        "extensions": {
            "local_ingest": True,
            "semantic_analysis_complete": False,
            "container_metadata": container_metadata,
        },
    }
    validate_timeline(timeline)
    return timeline


def ingest_video(
    source: str | Path,
    output_directory: str | Path,
    config: VideoIngestConfig | None = None,
) -> VideoIngestResult:
    """Decode a local video into evidence frames, audio and a valid Timeline."""

    av, Image, ImageChops, ImageStat = _imports()
    ingest_config = config or VideoIngestConfig()
    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    output_path = Path(output_directory).expanduser().resolve()
    frames_directory = output_path / "frames"
    frames_directory.mkdir(parents=True, exist_ok=True)

    asset_hash = binary_file_sha256(source_path)
    saved_frames: list[dict[str, Any]] = []
    generated_at = _utc_now()
    with av.open(str(source_path)) as container:
        video_streams = list(container.streams.video)
        if not video_streams:
            raise ValueError("input container has no video stream")
        stream = video_streams[0]
        duration_ms = _duration_ms(container, stream)
        next_interval_ms = 0
        last_saved_ms = -ingest_config.min_scene_gap_ms
        last_saved_thumb = None
        last_timestamp_ms = 0
        decoded_frames = 0
        for decoded_index, frame in enumerate(container.decode(stream)):
            decoded_frames += 1
            timestamp_ms = _frame_timestamp_ms(frame, stream, decoded_index)
            last_timestamp_ms = max(last_timestamp_ms, timestamp_ms)
            image = frame.to_image().convert("RGB")
            thumb = image.resize((64, 36), Image.Resampling.BILINEAR).convert("L")
            scene_score = (
                _difference_ratio(thumb, last_saved_thumb, ImageChops, ImageStat)
                if last_saved_thumb is not None
                else 1.0
            )
            interval_due = timestamp_ms >= next_interval_ms
            scene_due = (
                scene_score >= ingest_config.scene_threshold
                and timestamp_ms - last_saved_ms >= ingest_config.min_scene_gap_ms
            )
            if not saved_frames or interval_due or scene_due:
                target = frames_directory / f"frame-{len(saved_frames) + 1:04d}-{timestamp_ms:010d}ms.jpg"
                image.save(target, "JPEG", quality=ingest_config.jpeg_quality, optimize=True)
                frame_hash = binary_file_sha256(target)
                saved_frames.append(
                    {
                        "index": len(saved_frames),
                        "timestamp_ms": timestamp_ms,
                        "sample_reason": "first" if len(saved_frames) == 0 else "interval" if interval_due else "scene_change",
                        "scene_score": round(scene_score, 6),
                        "relative_path": str(target.relative_to(output_path)),
                        "artifact_ref": f"frame:{frame_hash[:20]}",
                        "content_hash": frame_hash,
                        "width": image.width,
                        "height": image.height,
                    }
                )
                last_saved_ms = timestamp_ms
                last_saved_thumb = thumb
                next_interval_ms = timestamp_ms + ingest_config.sample_interval_ms
                if len(saved_frames) >= ingest_config.max_frames:
                    break
        if not saved_frames:
            raise ValueError("video stream decoded zero frames")
        if duration_ms is None:
            rate = float(stream.average_rate) if stream.average_rate else 25.0
            duration_ms = max(1, last_timestamp_ms + int(1000 / rate))
        container_metadata = {
            "format": getattr(container.format, "name", None),
            "video_codec": getattr(getattr(stream, "codec_context", None), "name", None),
            "width": int(stream.width),
            "height": int(stream.height),
            "average_rate": str(stream.average_rate) if stream.average_rate else None,
            "decoded_frames": decoded_frames,
            "sampled_frames": len(saved_frames),
            "duration_ms": duration_ms,
            "audio_streams": len(container.streams.audio),
        }

    audio = None
    if ingest_config.extract_audio:
        audio = _extract_audio(source_path, output_path / "audio-16k-mono.wav", av)
    timeline = _build_timeline(
        asset_hash=asset_hash,
        source_name=source_path.name,
        duration_ms=duration_ms,
        frames=saved_frames,
        config=ingest_config,
        generated_at=generated_at,
        container_metadata=container_metadata,
    )
    manifest = {
        "schema_version": "audience-mirror.video-ingest/v0.1",
        "asset": timeline["asset"],
        "source_name": source_path.name,
        "source_extension": source_path.suffix.lower(),
        "generated_at": generated_at,
        "parser": "PyAV",
        "config": {
            field_name: getattr(ingest_config, field_name)
            for field_name in ingest_config.__dataclass_fields__
        },
        "container": container_metadata,
        "frames": saved_frames,
        "audio": audio,
        "limitations": [
            "本制品证明真实容器解码与证据定位，不等于完成视频语义理解。",
            "场景变化为像素差启发式；多模态模型和人工复核需要另行执行。",
        ],
    }
    write_json(output_path / "timeline.json", timeline)
    write_json(output_path / "ingest-manifest.json", manifest)
    return VideoIngestResult(timeline=timeline, manifest=manifest, output_directory=output_path)
