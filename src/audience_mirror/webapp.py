"""FastAPI workbench for the runnable Audience Mirror prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import importlib.util
import json
import mimetypes
import os
from pathlib import Path
import re
import shutil
from typing import Any
from uuid import uuid4

from .calibration import calibrate_traces
from .domain import RunConfig
from .environment import media_environment_spec
from .io import read_json, write_json
from .media.fusion import fuse_video_analysis
from .media.ingest import VideoIngestConfig, VideoIngestResult, ingest_video
from .media.source import SourceImportError, import_video_url
from .media.subtitles import attach_webvtt_subtitles
from .model_runtime import ModelSequentialRuntime, build_sequential_run_manifest
from .models.base import VideoAnalysisRequest
from .models.codex_frames import CodexFrameVideoProvider
from .models.gemini import GeminiVideoProvider
from .reasoning import ClaudeCodeJsonReasoner, CodexCliJsonReasoner
from .resources import resource_path, resource_root, workspace_root
from .runtime import DeterministicMediaRuntime
from .universe import SyntheticPersonaUniverse
from .validation import validate_timeline


WORKSPACE_ROOT = workspace_root()
REPOSITORY_ROOT = resource_root()
WEB_ROOT = resource_path("web")
ARTIFACT_ROOT = WORKSPACE_ROOT / "artifacts" / "workbench"
MAX_UPLOAD_BYTES = 1024 * 1024 * 1024
VIDEO_PROVIDER_MODELS = {
    "gemini": {"gemini-3.7-flash"},
    "codex-frames": {"gpt-5.6-sol"},
}
AGENT_MODELS = {
    "codex-cli": {"gpt-5.6-sol"},
    "claude-code": {"sonnet", "opus"},
}
EXPERIMENT_DIRECTORY_PATTERN = re.compile(r"^exp-[0-9a-f]{12}$")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class ExperimentRecord:
    experiment_id: str
    timeline: dict[str, Any]
    output_directory: Path | None = None
    source_path: Path | None = None
    source_metadata: dict[str, Any] = field(default_factory=dict)
    ingest: VideoIngestResult | None = None
    personas: list[dict[str, Any]] = field(default_factory=list)
    traces: list[dict[str, Any]] = field(default_factory=list)
    calibration: dict[str, Any] | None = None
    pool_size: int | None = None
    remote_processing_allowed: bool = False
    remote_processing_receipts: list[dict[str, Any]] = field(default_factory=list)
    rights_confirmed: bool = False
    status: str = "ready"
    runtime_mode: str = "not_run"
    run_manifest: dict[str, Any] | None = None


def _optional_json(path: Path, fallback: Any) -> Any:
    try:
        return read_json(path) if path.is_file() else fallback
    except (OSError, ValueError, TypeError):
        return fallback


def _source_path(output_directory: Path, manifest: dict[str, Any]) -> Path | None:
    source_directory = output_directory / "source"
    source_name = Path(str(manifest.get("source_name") or "")).name
    named_source = source_directory / source_name if source_name else None
    if named_source is not None and named_source.is_file():
        return named_source
    candidates = sorted(path for path in source_directory.iterdir() if path.is_file()) if source_directory.is_dir() else []
    return candidates[0] if len(candidates) == 1 else None


def _receipt_key(receipt: dict[str, Any]) -> tuple[Any, ...]:
    return (
        receipt.get("receipt_version"),
        receipt.get("provider"),
        receipt.get("model"),
        receipt.get("confirmed_at"),
        receipt.get("outcome"),
    )


def _load_remote_receipts(output_directory: Path) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for path in (
        output_directory / "analysis" / "remote-processing-receipts.json",
        output_directory / "run" / "remote-processing-receipts.json",
    ):
        payload = _optional_json(path, [])
        if not isinstance(payload, list):
            continue
        for receipt in payload:
            if not isinstance(receipt, dict):
                continue
            key = _receipt_key(receipt)
            if key not in seen:
                seen.add(key)
                receipts.append(receipt)
    return receipts


def _persist_record_state(record: ExperimentRecord) -> None:
    if record.output_directory is None:
        return
    write_json(
        record.output_directory / "experiment-state.json",
        {
            "schema_version": "audience-mirror.workbench-experiment/v0.1",
            "experiment_id": record.experiment_id,
            "status": record.status,
            "runtime_mode": record.runtime_mode,
            "rights_confirmed": record.rights_confirmed,
            "pool_size": record.pool_size,
            "updated_at": _utc_now(),
        },
    )


def _restore_record(output_directory: Path) -> ExperimentRecord | None:
    experiment_id = output_directory.name
    if not EXPERIMENT_DIRECTORY_PATTERN.fullmatch(experiment_id):
        return None
    try:
        root = ARTIFACT_ROOT.resolve()
        resolved_output = output_directory.resolve()
        if root not in resolved_output.parents:
            return None
        ingest_directory = resolved_output / "ingest"
        manifest = read_json(ingest_directory / "ingest-manifest.json")
        ingest_timeline_path = ingest_directory / "timeline.json"
        analysis_timeline_path = resolved_output / "analysis" / "timeline.json"
        timeline = read_json(analysis_timeline_path if analysis_timeline_path.is_file() else ingest_timeline_path)
        validate_timeline(timeline)
        if not isinstance(manifest, dict):
            return None
        source_metadata = _optional_json(resolved_output / "source-receipt.json", {})
        if not isinstance(source_metadata, dict):
            source_metadata = {}
        source_metadata = {
            "source_kind": source_metadata.get("source_kind", "restored_local_artifact"),
            "platform": source_metadata.get("platform", "local_file"),
            "display_url": source_metadata.get("display_url"),
            "title": source_metadata.get("title") or manifest.get("source_name") or experiment_id,
            "retrieval_method": source_metadata.get("retrieval_method", "local_artifact_recovery"),
            "retrieved_at": source_metadata.get("retrieved_at") or manifest.get("generated_at"),
            "sensitive_query_parameters_persisted": bool(source_metadata.get("sensitive_query_parameters_persisted", False)),
            "public_content_identifier_persisted": bool(source_metadata.get("public_content_identifier_persisted", False)),
        }
        personas = _optional_json(resolved_output / "run" / "personas.json", [])
        traces = _optional_json(resolved_output / "run" / "traces.json", [])
        run_manifest = _optional_json(resolved_output / "run" / "run-manifest.json", None)
        calibration = _optional_json(resolved_output / "calibration" / "report.json", None)
        state = _optional_json(resolved_output / "experiment-state.json", {})
        if not isinstance(personas, list) or not isinstance(traces, list):
            return None
        if not isinstance(state, dict):
            state = {}
        if calibration is not None:
            inferred_status = "calibrated"
        elif traces:
            inferred_status = "complete"
        elif analysis_timeline_path.is_file():
            inferred_status = "analyzed"
        else:
            inferred_status = "ingested"
        runtime = run_manifest.get("runtime", {}) if isinstance(run_manifest, dict) else {}
        inferred_runtime = runtime.get("mode") if isinstance(runtime, dict) else None
        if not inferred_runtime and traces:
            inferred_runtime = "restored_sequential_run"
        counts = run_manifest.get("counts", {}) if isinstance(run_manifest, dict) else {}
        pool_size = state.get("pool_size") or (counts.get("persona_pool_records") if isinstance(counts, dict) else None)
        return ExperimentRecord(
            experiment_id=experiment_id,
            timeline=timeline,
            output_directory=resolved_output,
            source_path=_source_path(resolved_output, manifest),
            source_metadata=source_metadata,
            ingest=VideoIngestResult(timeline=read_json(ingest_timeline_path), manifest=manifest, output_directory=ingest_directory),
            personas=personas,
            traces=traces,
            calibration=calibration if isinstance(calibration, dict) else None,
            pool_size=int(pool_size) if pool_size is not None else None,
            remote_processing_receipts=_load_remote_receipts(resolved_output),
            rights_confirmed=bool(state.get("rights_confirmed", True)),
            status=str(state.get("status") or inferred_status),
            runtime_mode=str(state.get("runtime_mode") or inferred_runtime or "not_run"),
            run_manifest=run_manifest if isinstance(run_manifest, dict) else None,
        )
    except (OSError, ValueError, TypeError, KeyError):
        return None


def _restore_records() -> dict[str, ExperimentRecord]:
    if not ARTIFACT_ROOT.is_dir():
        return {}
    records: dict[str, ExperimentRecord] = {}
    for output_directory in sorted(ARTIFACT_ROOT.iterdir()):
        if not output_directory.is_dir():
            continue
        record = _restore_record(output_directory)
        if record is not None:
            records[record.experiment_id] = record
    return records


def _record_updated_at(record: ExperimentRecord) -> str | None:
    if record.output_directory is None:
        return None
    state = _optional_json(record.output_directory / "experiment-state.json", {})
    if isinstance(state, dict) and state.get("updated_at"):
        return str(state["updated_at"])
    candidates = [
        record.output_directory / "calibration" / "report.json",
        record.output_directory / "run" / "run-manifest.json",
        record.output_directory / "run" / "traces.json",
        record.output_directory / "analysis" / "timeline.json",
        record.output_directory / "ingest" / "timeline.json",
    ]
    mtimes = [path.stat().st_mtime for path in candidates if path.is_file()]
    if not mtimes:
        return None
    return datetime.fromtimestamp(max(mtimes), UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _record_summary(record: ExperimentRecord) -> dict[str, Any]:
    events = [node for node in record.timeline.get("nodes", []) if node.get("level") == "event"]
    return {
        "experiment_id": record.experiment_id,
        "title": record.source_metadata.get("title") or record.experiment_id,
        "source_kind": record.source_metadata.get("source_kind"),
        "status": record.status,
        "runtime_mode": record.runtime_mode,
        "duration_ms": record.timeline.get("duration_ms"),
        "data_classification": record.timeline.get("data_handling", {}).get("data_classification"),
        "event_count": len(events),
        "deep_personas": len(record.personas),
        "trace_events": len(record.traces),
        "updated_at": _record_updated_at(record),
    }


def _frame_evidence(record: ExperimentRecord) -> list[dict[str, Any]]:
    if record.ingest is None:
        return []
    evidence: list[dict[str, Any]] = []
    root = record.ingest.output_directory.resolve()
    for frame in record.ingest.manifest.get("frames", []):
        if not isinstance(frame, dict):
            continue
        path = (root / str(frame.get("relative_path") or "")).resolve()
        timestamp_ms = frame.get("timestamp_ms")
        if root in path.parents and path.is_file() and isinstance(timestamp_ms, int):
            evidence.append(
                {
                    "path": str(path),
                    "t_ms": timestamp_ms,
                    "artifact_ref": frame.get("artifact_ref"),
                }
            )
    return evidence


def _attach_source_subtitles(
    record: ExperimentRecord,
    timeline: dict[str, Any],
) -> dict[str, Any]:
    subtitle = record.source_metadata.get("subtitle")
    if not isinstance(subtitle, dict) or record.output_directory is None:
        return timeline
    relative_path = Path(str(subtitle.get("relative_path") or ""))
    source_root = (record.output_directory / "source").resolve()
    path = (source_root / relative_path).resolve()
    if source_root not in path.parents or not path.is_file():
        return timeline
    return attach_webvtt_subtitles(timeline, path, subtitle)


def _demo_record() -> ExperimentRecord:
    timeline = read_json(resource_path("fixtures", "public-demo", "timeline.json"))
    config = RunConfig(
        experiment_id="exp-workbench-demo",
        run_id="run-workbench-demo",
        seed=20260820,
        pool_size=10_000,
        deep_count=6,
        sweep_count=12,
        projection_count=10_000,
    )
    universe = SyntheticPersonaUniverse(config.pool_size, config.seed)
    personas = universe.cohort(config.deep_count)
    traces = DeterministicMediaRuntime().run_deep(timeline, personas, config)
    return ExperimentRecord(
        experiment_id="demo",
        timeline=timeline,
        personas=[persona.to_dict() for persona in personas],
        traces=traces,
        pool_size=config.pool_size,
        source_metadata={
            "source_kind": "fixture",
            "platform": "audience_mirror",
            "display_url": None,
            "title": "公开合成 Timeline Fixture",
            "retrieval_method": "bundled_fixture",
        },
        rights_confirmed=True,
        status="complete",
        runtime_mode="deterministic_fixture",
    )


def _public_record(record: ExperimentRecord) -> dict[str, Any]:
    timeline_events = sorted(
        (node for node in record.timeline["nodes"] if node["level"] == "event"),
        key=lambda node: (node["t_start_ms"], node["node_id"]),
    )
    frame_urls: dict[str, str] = {}
    if record.ingest is not None:
        for index, frame in enumerate(record.ingest.manifest["frames"]):
            frame_urls[frame["artifact_ref"]] = f"/api/experiments/{record.experiment_id}/frames/{index}"
    audio_url = None
    if record.ingest is not None and record.ingest.manifest.get("audio"):
        audio_url = f"/api/experiments/{record.experiment_id}/media/audio"
    media_url = (
        f"/api/experiments/{record.experiment_id}/media/video"
        if record.source_path is not None
        else None
    )
    video_model = record.timeline.get("extensions", {}).get("video_model", {})
    provider_warnings = video_model.get("warnings", []) if isinstance(video_model, dict) else []
    subtitle_track = record.timeline.get("extensions", {}).get("subtitle_track", {})
    subtitle_limitations = (
        subtitle_track.get("limitations", []) if isinstance(subtitle_track, dict) else []
    )
    return {
        "experiment_id": record.experiment_id,
        "status": record.status,
        "runtime_mode": record.runtime_mode,
        "rights_confirmed": record.rights_confirmed,
        "remote_processing_allowed": record.remote_processing_allowed,
        "timeline": record.timeline,
        "events": timeline_events,
        "environment": media_environment_spec(record.timeline),
        "personas": record.personas,
        "traces": record.traces,
        "calibration": record.calibration,
        "frame_urls": frame_urls,
        "media_url": media_url,
        "audio_url": audio_url,
        "source_name": record.source_path.name if record.source_path else None,
        "source": record.source_metadata,
        "remote_processing_receipts": record.remote_processing_receipts,
        "run_manifest": record.run_manifest,
        "counts": {
            "persona_pool_records": record.pool_size,
            "deep_personas": len(record.personas),
            "deep_trace_events": len(record.traces),
            "human_participants": (
                record.calibration.get("scope", {}).get("human_participants", 0)
                if record.calibration
                else 0
            ),
        },
        "limitations": [
            "界面中的注意、情绪、理解、购买等数值均为预测代理量。",
            "Persona 数不等于真人样本量；只有导入同任务 Human Anchors 后才能报告校准结果。",
            *[str(warning) for warning in provider_warnings if warning],
            *[str(warning) for warning in subtitle_limitations if warning],
        ],
    }


def create_app() -> Any:
    try:
        from fastapi import FastAPI, File, Form, HTTPException, UploadFile
        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles
        from starlette.concurrency import run_in_threadpool
    except ImportError as exc:
        raise RuntimeError(
            "Web 工作台需要 web extra：python -m pip install -e '.[web]'"
        ) from exc

    app = FastAPI(title="Audience Mirror Workbench", version="0.2.0a3")
    records: dict[str, ExperimentRecord] = {"demo": _demo_record(), **_restore_records()}

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {
            "ok": True,
            "version": "0.2.0a3",
            "capabilities": {
                "local_video_decode": bool(importlib.util.find_spec("av") and importlib.util.find_spec("PIL")),
                "direct_video_url": True,
                "platform_video_url": importlib.util.find_spec("yt_dlp") is not None,
                "gemini_native_video": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
                "codex_frame_analysis": shutil.which("codex") is not None,
                "claude_code_cli": shutil.which("claude") is not None,
                "codex_cli": shutil.which("codex") is not None,
                "human_calibration": True,
                "environment_contract": True,
            },
            "privacy": {
                "remote_processing_default": False,
                "max_upload_bytes": MAX_UPLOAD_BYTES,
                "supported_link_sources": ["direct_http_video", "youtube", "bilibili", "douyin"],
                "sensitive_source_query_parameters_persisted": False,
                "public_content_identifiers_may_be_persisted": True,
            },
        }

    @app.get("/api/experiments")
    def list_experiments() -> dict[str, Any]:
        summaries = [_record_summary(record) for key, record in records.items() if key != "demo"]
        summaries.sort(key=lambda item: (item.get("updated_at") or "", item["experiment_id"]), reverse=True)
        return {
            "experiments": summaries,
            "count": len(summaries),
            "persistence": "local_artifacts",
        }

    @app.get("/api/experiments/{experiment_id}")
    def get_experiment(experiment_id: str) -> dict[str, Any]:
        record = records.get(experiment_id)
        if record is None:
            raise HTTPException(status_code=404, detail="实验不存在或服务重启后已失效。")
        return _public_record(record)

    @app.post("/api/experiments")
    async def create_experiment(
        file = File(None),
        source_url: str | None = Form(None),
        rights_confirmed: bool = Form(False),
        classification: str = Form("public"),
        export_policy: str = Form("authorized"),
        sample_interval_ms: int = Form(5_000),
        scene_threshold: float = Form(0.24),
    ) -> dict[str, Any]:
        if not rights_confirmed:
            raise HTTPException(status_code=400, detail="必须先确认素材权利与测试授权。")
        if classification not in {"public", "internal", "confidential", "restricted"}:
            raise HTTPException(status_code=400, detail="不支持的数据分类。")
        has_file = file is not None and bool(getattr(file, "filename", None))
        normalized_url = (source_url or "").strip()
        has_url = bool(normalized_url)
        if has_file == has_url:
            raise HTTPException(status_code=400, detail="请粘贴一个视频链接，或上传一个视频文件；两者只选其一。")
        experiment_id = f"exp-{uuid4().hex[:12]}"
        output_directory = ARTIFACT_ROOT / experiment_id
        upload_directory = output_directory / "source"
        upload_directory.mkdir(parents=True, exist_ok=True)
        if has_url:
            try:
                source_import = await run_in_threadpool(
                    import_video_url,
                    normalized_url,
                    upload_directory,
                    max_bytes=MAX_UPLOAD_BYTES,
                )
            except SourceImportError as exc:
                shutil.rmtree(output_directory, ignore_errors=True)
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            except Exception:
                shutil.rmtree(output_directory, ignore_errors=True)
                raise
            source_path = source_import.source_path
            source_metadata = source_import.metadata
        else:
            safe_name = Path(file.filename or "uploaded-video.bin").name
            source_path = upload_directory / safe_name
            total = 0
            try:
                with source_path.open("wb") as target:
                    while True:
                        chunk = await file.read(1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_UPLOAD_BYTES:
                            raise HTTPException(status_code=413, detail="视频超过 1 GiB 原型限制。")
                        target.write(chunk)
            except Exception:
                shutil.rmtree(output_directory, ignore_errors=True)
                raise
            source_metadata = {
                "source_kind": "upload",
                "platform": "local_file",
                "display_url": None,
                "transport_secure": None,
                "retrieval_method": "multipart_upload",
                "retrieved_at": _utc_now(),
                "content_type": getattr(file, "content_type", None),
                "downloaded_bytes": total,
                "title": safe_name,
                "sensitive_query_parameters_persisted": False,
                "public_content_identifier_persisted": False,
            }
        try:
            ingest_result = await run_in_threadpool(
                ingest_video,
                source_path,
                output_directory / "ingest",
                VideoIngestConfig(
                    sample_interval_ms=sample_interval_ms,
                    scene_threshold=scene_threshold,
                    extract_audio=True,
                    data_classification=classification,
                    export_policy=export_policy,
                    retention_class="workbench-prototype",
                    rights_manifest_id=f"rights:{experiment_id}",
                ),
            )
        except Exception as exc:
            shutil.rmtree(output_directory, ignore_errors=True)
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        record = ExperimentRecord(
            experiment_id=experiment_id,
            timeline=ingest_result.timeline,
            output_directory=output_directory,
            source_path=source_path,
            source_metadata=source_metadata,
            ingest=ingest_result,
            rights_confirmed=True,
            status="ingested",
        )
        try:
            write_json(output_directory / "source-receipt.json", source_metadata)
            _persist_record_state(record)
        except Exception:
            shutil.rmtree(output_directory, ignore_errors=True)
            raise
        records[experiment_id] = record
        return _public_record(record)

    @app.post("/api/experiments/{experiment_id}/analyze")
    def analyze_experiment(
        experiment_id: str,
        provider: str = Form("gemini"),
        model: str = Form("gemini-3.7-flash"),
        task: str | None = Form(None),
        remote_processing_confirmed: bool = Form(False),
        provider_policy_confirmed: bool = Form(False),
    ) -> dict[str, Any]:
        record = records.get(experiment_id)
        if record is None:
            raise HTTPException(status_code=404, detail="实验不存在。")
        if record.source_path is None:
            raise HTTPException(status_code=400, detail="公开 Fixture 没有可发送的原始视频。")
        if not remote_processing_confirmed or not provider_policy_confirmed:
            raise HTTPException(
                status_code=403,
                detail="本次调用尚未同时确认远程处理与 Provider 数据政策。",
            )
        if provider not in VIDEO_PROVIDER_MODELS or model not in VIDEO_PROVIDER_MODELS[provider]:
            raise HTTPException(status_code=400, detail="Provider 与模型组合不在当前已审查的 Adapter 允许列表。")
        classification = record.timeline["data_handling"]["data_classification"]
        if classification not in {"public", "internal"}:
            raise HTTPException(
                status_code=403,
                detail="公有视频分析路由默认拒绝机密／受限素材；请使用经确认的私有部署路由。",
            )
        is_native_video = provider == "gemini"
        receipt = {
            "receipt_version": "audience-mirror.remote-processing/v0.1",
            "provider": provider,
            "model": model,
            "data_classification": classification,
            "payload_scope": (
                "full_video_with_audio"
                if is_native_video
                else "up_to_12_timestamped_local_jpeg_frames; original_video_and_audio_not_sent"
            ),
            "processing_region": "provider_managed_public_api" if is_native_video else "provider_managed_cli_session",
            "retention": (
                "remote_file_delete_requested_after_call; service logs follow current provider terms"
                if is_native_video
                else "follows authenticated CLI account and current provider terms"
            ),
            "training_use": "not asserted by this prototype; current provider policy review acknowledged",
            "policy_refs": [
                "https://ai.google.dev/gemini-api/terms"
                if is_native_video
                else "https://openai.com/policies/service-terms/",
            ],
            "confirmed_at": _utc_now(),
            "outcome": "started",
        }
        record.remote_processing_allowed = True
        record.remote_processing_receipts.append(receipt)
        try:
            video_provider = (
                GeminiVideoProvider(model_id=model)
                if is_native_video
                else CodexFrameVideoProvider(model_id=model, effort="xhigh", max_images=12)
            )
            result = video_provider.analyze(
                VideoAnalysisRequest(
                    video_path=record.source_path,
                    asset_hash=record.timeline["asset"]["content_hash"],
                    duration_ms=record.timeline["duration_ms"],
                    task_prompt=task,
                    data_classification=record.timeline["data_handling"]["data_classification"],
                    allow_remote_processing=True,
                    extensions={"frame_evidence": _frame_evidence(record)},
                )
            )
            base_timeline = record.ingest.timeline if record.ingest is not None else record.timeline
            record.timeline = fuse_video_analysis(base_timeline, result)
            record.timeline = _attach_source_subtitles(record, record.timeline)
            record.status = "analyzed"
            receipt["outcome"] = "complete"
            if record.output_directory:
                write_json(record.output_directory / "analysis" / "model-result.json", result.to_dict())
                write_json(record.output_directory / "analysis" / "timeline.json", record.timeline)
        except Exception as exc:
            receipt["outcome"] = "failed"
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        finally:
            record.remote_processing_allowed = False
            if record.output_directory:
                write_json(
                    record.output_directory / "analysis" / "remote-processing-receipts.json",
                    record.remote_processing_receipts,
                )
                _persist_record_state(record)
        return _public_record(record)

    @app.post("/api/experiments/{experiment_id}/run")
    def run_experiment(
        experiment_id: str,
        runtime_mode: str = Form("deterministic"),
        persona_count: int = Form(6),
        reasoner: str = Form("codex-cli"),
        model: str = Form("gpt-5.6-sol"),
        effort: str = Form("xhigh"),
        max_budget_usd: float = Form(0.1),
        agent_remote_processing_confirmed: bool = Form(False),
        agent_provider_policy_confirmed: bool = Form(False),
    ) -> dict[str, Any]:
        record = records.get(experiment_id)
        if record is None:
            raise HTTPException(status_code=404, detail="实验不存在。")
        if not 1 <= persona_count <= 32:
            raise HTTPException(status_code=400, detail="Deep Persona 数必须在 1 到 32 之间。")
        events = [node for node in record.timeline["nodes"] if node["level"] == "event"]
        call_plan = len(events) * persona_count
        if runtime_mode == "model" and call_plan > 16:
            raise HTTPException(
                status_code=400,
                detail=f"当前模型调用计划为 {call_plan} 次，超过原型上限 16；请减少 Persona 或先合并时间片。",
            )
        if runtime_mode == "model":
            if not agent_remote_processing_confirmed or not agent_provider_policy_confirmed:
                raise HTTPException(
                    status_code=403,
                    detail="模型顺序体验尚未同时确认远程处理与 Provider 数据政策。",
                )
            if record.timeline["data_handling"]["data_classification"] not in {"public", "internal"}:
                raise HTTPException(
                    status_code=403,
                    detail="公有 CLI Reasoner 默认拒绝机密／受限 Timeline；请使用经确认的私有部署路由。",
                )
            if reasoner not in AGENT_MODELS or model not in AGENT_MODELS[reasoner]:
                raise HTTPException(status_code=400, detail="Reasoner 与模型组合不在当前允许列表。")
            if effort not in {"low", "medium", "high", "xhigh", "max"}:
                raise HTTPException(status_code=400, detail="不支持的推理强度。")
            agent_receipt: dict[str, Any] | None = {
                "receipt_version": "audience-mirror.agent-remote-processing/v0.1",
                "provider": reasoner,
                "model": model,
                "effort": effort,
                "data_classification": record.timeline["data_handling"]["data_classification"],
                "payload_scope": "timeline_observations_persona_and_prior_memory; original_media_not_sent",
                "processing_region": "provider_managed_cli_session",
                "retention": "follows authenticated CLI account and current provider terms",
                "training_use": "not asserted by this prototype; provider policy review acknowledged",
                "confirmed_at": _utc_now(),
                "outcome": "started",
            }
            record.remote_processing_receipts.append(agent_receipt)
        else:
            agent_receipt = None
        pool_size = max(10_000, persona_count + 1)
        config = RunConfig(
            experiment_id=record.experiment_id,
            run_id=f"run-{uuid4().hex[:10]}",
            seed=20260820,
            pool_size=pool_size,
            deep_count=persona_count,
            sweep_count=1,
            projection_count=pool_size,
        )
        universe = SyntheticPersonaUniverse(pool_size, config.seed)
        personas = universe.cohort(persona_count)
        try:
            if runtime_mode == "deterministic":
                runtime = DeterministicMediaRuntime()
                traces = runtime.run_deep(record.timeline, personas, config)
                record.runtime_mode = "deterministic_engineering_baseline"
                manifest_kwargs = {
                    "producer": runtime.producer,
                    "code_version": runtime.code_version,
                }
            elif runtime_mode == "model":
                if reasoner == "claude-code":
                    reasoner_client = ClaudeCodeJsonReasoner(
                        model_id=model,
                        effort=effort,
                        max_budget_usd=max_budget_usd,
                    )
                    effective_budget = max_budget_usd
                else:
                    reasoner_client = CodexCliJsonReasoner(model_id=model, effort=effort)
                    effective_budget = None
                runtime = ModelSequentialRuntime(reasoner_client)
                traces = runtime.run_deep(record.timeline, personas, config)
                record.runtime_mode = "model_sequential"
                manifest_kwargs = {
                    "producer": runtime.producer,
                    "code_version": runtime.code_version,
                    "model_provider": reasoner_client.provider,
                    "model_id": reasoner_client.model_id,
                    "effort": reasoner_client.effort,
                    "max_budget_usd": effective_budget,
                }
            else:
                raise ValueError("runtime_mode must be deterministic or model")
        except Exception as exc:
            if agent_receipt is not None:
                agent_receipt["outcome"] = "failed"
                if record.output_directory:
                    write_json(
                        record.output_directory / "run" / "remote-processing-receipts.json",
                        record.remote_processing_receipts,
                    )
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        record.personas = [persona.to_dict() for persona in personas]
        record.traces = traces
        record.pool_size = pool_size
        record.run_manifest = build_sequential_run_manifest(
            timeline=record.timeline,
            personas=personas,
            traces=traces,
            config=config,
            runtime_mode=record.runtime_mode,
            **manifest_kwargs,
        )
        if agent_receipt is not None:
            agent_receipt["outcome"] = "complete"
        record.status = "complete"
        if record.output_directory:
            write_json(record.output_directory / "run" / "personas.json", record.personas)
            write_json(record.output_directory / "run" / "traces.json", traces)
            write_json(record.output_directory / "run" / "run-manifest.json", record.run_manifest)
            if agent_receipt is not None:
                write_json(
                    record.output_directory / "run" / "remote-processing-receipts.json",
                    record.remote_processing_receipts,
                )
            _persist_record_state(record)
        return _public_record(record)

    @app.post("/api/experiments/{experiment_id}/calibrate")
    async def calibrate_experiment(
        experiment_id: str,
        file = File(...),
        agent_ab_direction: str | None = Form(None),
    ) -> dict[str, Any]:
        record = records.get(experiment_id)
        if record is None:
            raise HTTPException(status_code=404, detail="实验不存在。")
        if not record.traces:
            raise HTTPException(status_code=400, detail="请先运行 Agent 顺序体验。")
        try:
            payload = json.loads((await file.read()).decode("utf-8"))
            anchors = payload.get("anchors", []) if isinstance(payload, dict) else payload
            if not isinstance(anchors, list):
                raise ValueError("Human Anchor 文件必须是 JSON 数组或含 anchors 的对象。")
            report = calibrate_traces(
                record.traces,
                anchors,
                agent_ab_direction=agent_ab_direction,
            )
        except Exception as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        record.calibration = report
        if record.output_directory:
            write_json(record.output_directory / "calibration" / "report.json", report)
            _persist_record_state(record)
        return _public_record(record)

    @app.get("/api/experiments/{experiment_id}/frames/{frame_index}")
    def get_frame(experiment_id: str, frame_index: int) -> Any:
        record = records.get(experiment_id)
        if record is None or record.ingest is None:
            raise HTTPException(status_code=404, detail="帧证据不存在。")
        frames = record.ingest.manifest["frames"]
        if frame_index < 0 or frame_index >= len(frames):
            raise HTTPException(status_code=404, detail="帧索引越界。")
        path = (record.ingest.output_directory / frames[frame_index]["relative_path"]).resolve()
        if record.ingest.output_directory.resolve() not in path.parents or not path.is_file():
            raise HTTPException(status_code=404, detail="帧制品不可用。")
        return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=60"})

    @app.get("/api/experiments/{experiment_id}/media/video")
    def get_source_video(experiment_id: str) -> Any:
        record = records.get(experiment_id)
        if record is None or record.source_path is None:
            raise HTTPException(status_code=404, detail="原视频证据不存在。")
        path = record.source_path.resolve()
        if record.output_directory is None or record.output_directory.resolve() not in path.parents or not path.is_file():
            raise HTTPException(status_code=404, detail="原视频制品不可用。")
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return FileResponse(
            path,
            media_type=media_type,
            filename=path.name,
            content_disposition_type="inline",
            headers={"Cache-Control": "private, no-store", "Accept-Ranges": "bytes"},
        )

    @app.get("/api/experiments/{experiment_id}/media/audio")
    def get_extracted_audio(experiment_id: str) -> Any:
        record = records.get(experiment_id)
        audio = record.ingest.manifest.get("audio") if record and record.ingest else None
        if record is None or record.ingest is None or not audio:
            raise HTTPException(status_code=404, detail="抽取音轨不存在。")
        path = (record.ingest.output_directory / audio["relative_path"]).resolve()
        if record.ingest.output_directory.resolve() not in path.parents or not path.is_file():
            raise HTTPException(status_code=404, detail="抽取音轨制品不可用。")
        return FileResponse(
            path,
            media_type="audio/wav",
            filename=path.name,
            content_disposition_type="inline",
            headers={"Cache-Control": "private, no-store", "Accept-Ranges": "bytes"},
        )

    if not WEB_ROOT.is_dir():
        raise RuntimeError(f"web assets are missing: {WEB_ROOT}")
    app.mount("/", StaticFiles(directory=WEB_ROOT, html=True), name="web")
    return app


def run_server(host: str = "127.0.0.1", port: int = 8765, reload: bool = False) -> None:
    try:
        import uvicorn
    except ImportError as exc:
        raise RuntimeError(
            "Web 工作台需要 web extra：python -m pip install -e '.[web]'"
        ) from exc
    uvicorn.run("audience_mirror.webapp:create_app", factory=True, host=host, port=port, reload=reload)
