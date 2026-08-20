"""FastAPI workbench for the runnable Audience Mirror prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import importlib.util
import json
import mimetypes
import os
from pathlib import Path
import shutil
from typing import Any
from uuid import uuid4

from .calibration import calibrate_traces
from .domain import RunConfig
from .environment import media_environment_spec
from .io import read_json, write_json
from .media.fusion import fuse_video_analysis
from .media.ingest import VideoIngestConfig, VideoIngestResult, ingest_video
from .model_runtime import ModelSequentialRuntime
from .models.base import VideoAnalysisRequest
from .models.gemini import GeminiVideoProvider
from .reasoning import ClaudeCodeJsonReasoner
from .runtime import DeterministicMediaRuntime
from .universe import SyntheticPersonaUniverse
from .validation import validate_timeline


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
WEB_ROOT = REPOSITORY_ROOT / "web"
ARTIFACT_ROOT = REPOSITORY_ROOT / "artifacts" / "workbench"
MAX_UPLOAD_BYTES = 1024 * 1024 * 1024
GEMINI_MODELS = {"gemini-3.7-flash"}


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class ExperimentRecord:
    experiment_id: str
    timeline: dict[str, Any]
    output_directory: Path | None = None
    source_path: Path | None = None
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


def _demo_record() -> ExperimentRecord:
    timeline = read_json(REPOSITORY_ROOT / "fixtures" / "public-demo" / "timeline.json")
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
        "remote_processing_receipts": record.remote_processing_receipts,
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
        ],
    }


def create_app() -> Any:
    try:
        from fastapi import FastAPI, File, Form, HTTPException, UploadFile
        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles
    except ImportError as exc:
        raise RuntimeError(
            "Web 工作台需要 web extra：python -m pip install -e '.[web]'"
        ) from exc

    app = FastAPI(title="Audience Mirror Workbench", version="0.2.0a1")
    records: dict[str, ExperimentRecord] = {"demo": _demo_record()}

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {
            "ok": True,
            "version": "0.2.0a1",
            "capabilities": {
                "local_video_decode": bool(importlib.util.find_spec("av") and importlib.util.find_spec("PIL")),
                "gemini_native_video": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
                "claude_code_cli": shutil.which("claude") is not None,
                "human_calibration": True,
                "environment_contract": True,
            },
            "privacy": {
                "remote_processing_default": False,
                "max_upload_bytes": MAX_UPLOAD_BYTES,
            },
        }

    @app.get("/api/experiments/{experiment_id}")
    def get_experiment(experiment_id: str) -> dict[str, Any]:
        record = records.get(experiment_id)
        if record is None:
            raise HTTPException(status_code=404, detail="实验不存在或服务重启后已失效。")
        return _public_record(record)

    @app.post("/api/experiments")
    async def create_experiment(
        file = File(...),
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
        experiment_id = f"exp-{uuid4().hex[:12]}"
        output_directory = ARTIFACT_ROOT / experiment_id
        upload_directory = output_directory / "source"
        upload_directory.mkdir(parents=True, exist_ok=True)
        safe_name = Path(file.filename or "uploaded-video.bin").name
        source_path = upload_directory / safe_name
        total = 0
        with source_path.open("wb") as target:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    target.close()
                    source_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=413, detail="视频超过 1 GiB 原型限制。")
                target.write(chunk)
        try:
            ingest_result = ingest_video(
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
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        record = ExperimentRecord(
            experiment_id=experiment_id,
            timeline=ingest_result.timeline,
            output_directory=output_directory,
            source_path=source_path,
            ingest=ingest_result,
            rights_confirmed=True,
            status="ingested",
        )
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
        if provider != "gemini":
            raise HTTPException(status_code=400, detail="当前原型只启用 Gemini 原生视频 Adapter。")
        if model not in GEMINI_MODELS:
            raise HTTPException(status_code=400, detail="模型不在当前已审查的 Adapter 允许列表。")
        classification = record.timeline["data_handling"]["data_classification"]
        if classification not in {"public", "internal"}:
            raise HTTPException(
                status_code=403,
                detail="Gemini 公有 API 路由默认拒绝机密／受限素材；请使用经确认的私有部署路由。",
            )
        receipt = {
            "receipt_version": "audience-mirror.remote-processing/v0.1",
            "provider": provider,
            "model": model,
            "data_classification": classification,
            "processing_region": "provider_managed_public_api",
            "retention": "remote_file_delete_requested_after_call; service logs follow current provider terms",
            "training_use": "not asserted by this prototype; current provider policy review acknowledged",
            "policy_refs": [
                "https://ai.google.dev/gemini-api/terms",
            ],
            "confirmed_at": _utc_now(),
            "outcome": "started",
        }
        record.remote_processing_allowed = True
        record.remote_processing_receipts.append(receipt)
        try:
            result = GeminiVideoProvider(model_id=model).analyze(
                VideoAnalysisRequest(
                    video_path=record.source_path,
                    asset_hash=record.timeline["asset"]["content_hash"],
                    duration_ms=record.timeline["duration_ms"],
                    task_prompt=task,
                    data_classification=record.timeline["data_handling"]["data_classification"],
                    allow_remote_processing=True,
                )
            )
            record.timeline = fuse_video_analysis(record.timeline, result)
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
        return _public_record(record)

    @app.post("/api/experiments/{experiment_id}/run")
    def run_experiment(
        experiment_id: str,
        runtime_mode: str = Form("deterministic"),
        persona_count: int = Form(6),
        model: str = Form("sonnet"),
        max_budget_usd: float = Form(0.1),
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
                traces = DeterministicMediaRuntime().run_deep(record.timeline, personas, config)
                record.runtime_mode = "deterministic_engineering_baseline"
            elif runtime_mode == "model":
                reasoner = ClaudeCodeJsonReasoner(model_id=model, max_budget_usd=max_budget_usd)
                traces = ModelSequentialRuntime(reasoner).run_deep(record.timeline, personas, config)
                record.runtime_mode = "model_sequential"
            else:
                raise ValueError("runtime_mode must be deterministic or model")
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        record.personas = [persona.to_dict() for persona in personas]
        record.traces = traces
        record.pool_size = pool_size
        record.status = "complete"
        if record.output_directory:
            write_json(record.output_directory / "run" / "personas.json", record.personas)
            write_json(record.output_directory / "run" / "traces.json", traces)
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
