"""Command-line interface for the local Audience Mirror baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .adapters.matraix import MatrAixAdapter
from .calibration import calibrate_traces
from .demo import run_public_demo
from .domain import RunConfig
from .environment import media_environment_spec, validate_environment_spec
from .io import binary_file_sha256, read_json, write_json
from .media.fusion import fuse_video_analysis
from .media.ingest import VideoIngestConfig, ingest_video
from .model_runtime import ModelSequentialRuntime, build_sequential_run_manifest
from .models.base import VideoAnalysisRequest
from .models.gemini import GeminiVideoProvider
from .reasoning import ClaudeCodeJsonReasoner, CodexCliJsonReasoner
from .resources import resource_path
from .universe import SyntheticPersonaUniverse
from .validation import ContractValidationError, validate_timeline, validate_trace_stream


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audience-mirror",
        description="Run and validate evidence-linked synthetic audience experiments.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="Run the zero-cost public synthetic fixture")
    demo.add_argument(
        "--timeline",
        default=str(resource_path("fixtures", "public-demo", "timeline.json")),
    )
    demo.add_argument("--output", default="artifacts/public-demo")
    demo.add_argument("--seed", type=int, default=20260819)
    demo.add_argument("--pool-size", type=int, default=10_000)
    demo.add_argument("--deep-count", type=int, default=12)
    demo.add_argument("--sweep-count", type=int, default=100)
    demo.add_argument("--projection-count", type=int, default=10_000)

    validate = subparsers.add_parser("validate", help="Validate Timeline or Trace artifacts")
    validate_subparsers = validate.add_subparsers(dest="artifact_type", required=True)
    validate_timeline_parser = validate_subparsers.add_parser("timeline")
    validate_timeline_parser.add_argument("path")
    validate_traces_parser = validate_subparsers.add_parser("traces")
    validate_traces_parser.add_argument("path")
    validate_traces_parser.add_argument("--timeline", required=True)

    doctor = subparsers.add_parser("matraix-doctor", help="Inspect an external MatrAIx checkout")
    doctor.add_argument("--repo")

    ingest = subparsers.add_parser("ingest-video", help="Decode a real local video into Timeline evidence")
    ingest.add_argument("path")
    ingest.add_argument("--output", default="artifacts/video-ingest")
    ingest.add_argument("--sample-interval-ms", type=int, default=5_000)
    ingest.add_argument("--scene-threshold", type=float, default=0.24)
    ingest.add_argument("--max-frames", type=int, default=240)
    ingest.add_argument("--no-audio", action="store_true")
    ingest.add_argument("--classification", choices=["public", "internal", "confidential", "restricted"], default="public")
    ingest.add_argument("--export-policy", choices=["no_export", "redacted_only", "authorized"], default="authorized")
    ingest.add_argument("--rights-manifest-id", default="rights-local-prototype")

    environment = subparsers.add_parser("environment-spec", help="Build the generic Environment Contract from a Timeline")
    environment.add_argument("--timeline", required=True)
    environment.add_argument("--output")

    analyze = subparsers.add_parser("analyze-video", help="Call a native video model and fuse its evidence into a Timeline")
    analyze.add_argument("path")
    analyze.add_argument("--timeline", required=True)
    analyze.add_argument("--output", default="artifacts/video-analysis")
    analyze.add_argument("--provider", choices=["gemini"], default="gemini")
    analyze.add_argument("--model", default="gemini-3.7-flash")
    analyze.add_argument("--language", default="zh-CN")
    analyze.add_argument("--task")
    analyze.add_argument("--allow-remote-processing", action="store_true")

    run_agent = subparsers.add_parser("run-agent", help="Run real structured model calls over a Timeline sequentially")
    run_agent.add_argument("--timeline", required=True)
    run_agent.add_argument("--output", default="artifacts/model-run/traces.json")
    run_agent.add_argument(
        "--reasoner",
        choices=["claude-code", "codex-cli"],
        default="codex-cli",
    )
    run_agent.add_argument("--model", default="gpt-5.6-sol")
    run_agent.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], default="xhigh")
    run_agent.add_argument("--max-budget-usd", type=float, default=0.25)
    run_agent.add_argument(
        "--max-model-calls",
        type=int,
        default=16,
        help="Hard cap for Persona x event structured model calls",
    )
    run_agent.add_argument("--persona-count", type=int, default=1)
    run_agent.add_argument("--seed", type=int, default=20260820)
    run_agent.add_argument(
        "--allow-remote-processing",
        action="store_true",
        help="Confirm that Timeline observations and Persona context may be sent to the selected remote model",
    )

    calibrate = subparsers.add_parser("calibrate", help="Compare Agent traces with consent-linked Human Anchors")
    calibrate.add_argument("--traces", required=True)
    calibrate.add_argument("--anchors", required=True)
    calibrate.add_argument("--output", default="artifacts/calibration/report.json")
    calibrate.add_argument("--top-k", type=int, default=10)
    calibrate.add_argument(
        "--agent-ab-direction",
        choices=["variant_a", "variant_b", "no_difference"],
    )

    serve = subparsers.add_parser("serve", help="Start the local interactive workbench")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--reload", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            config = RunConfig(
                seed=args.seed,
                pool_size=args.pool_size,
                deep_count=args.deep_count,
                sweep_count=args.sweep_count,
                projection_count=args.projection_count,
            )
            _print_json(
                run_public_demo(
                    timeline_path=Path(args.timeline),
                    output_directory=Path(args.output),
                    config=config,
                )
            )
            return 0

        if args.command == "validate" and args.artifact_type == "timeline":
            validate_timeline(read_json(args.path))
            _print_json({"ok": True, "artifact": str(Path(args.path).resolve()), "type": "timeline"})
            return 0

        if args.command == "validate" and args.artifact_type == "traces":
            validate_trace_stream(read_json(args.path), read_json(args.timeline))
            _print_json({"ok": True, "artifact": str(Path(args.path).resolve()), "type": "traces"})
            return 0

        if args.command == "matraix-doctor":
            report = MatrAixAdapter(args.repo).doctor()
            _print_json(report.to_dict())
            return 0 if report.available else 2

        if args.command == "ingest-video":
            result = ingest_video(
                args.path,
                args.output,
                VideoIngestConfig(
                    sample_interval_ms=args.sample_interval_ms,
                    scene_threshold=args.scene_threshold,
                    max_frames=args.max_frames,
                    extract_audio=not args.no_audio,
                    data_classification=args.classification,
                    export_policy=args.export_policy,
                    rights_manifest_id=args.rights_manifest_id,
                ),
            )
            _print_json(
                {
                    "ok": True,
                    "timeline": str(result.output_directory / "timeline.json"),
                    "manifest": str(result.output_directory / "ingest-manifest.json"),
                    "sampled_frames": len(result.manifest["frames"]),
                    "duration_ms": result.timeline["duration_ms"],
                }
            )
            return 0

        if args.command == "environment-spec":
            spec = media_environment_spec(read_json(args.timeline))
            validate_environment_spec(spec)
            if args.output:
                write_json(args.output, spec)
            _print_json(spec)
            return 0

        if args.command == "analyze-video":
            timeline = read_json(args.timeline)
            validate_timeline(timeline)
            if not args.allow_remote_processing:
                raise PermissionError(
                    "allow-remote-processing 未确认；未把 Timeline 观察与 Persona 上下文发送给远程模型。"
                )
            if timeline["data_handling"]["data_classification"] not in {"public", "internal"}:
                raise PermissionError(
                    "Claude Code／Codex CLI 公有远程路由默认拒绝 confidential/restricted Timeline。"
                )
            source = Path(args.path).expanduser().resolve()
            source_hash = binary_file_sha256(source)
            if source_hash != timeline["asset"]["content_hash"]:
                raise ValueError("video content hash does not match the supplied Timeline asset")
            provider = GeminiVideoProvider(model_id=args.model)
            result = provider.analyze(
                VideoAnalysisRequest(
                    video_path=source,
                    asset_hash=source_hash,
                    duration_ms=timeline["duration_ms"],
                    language=args.language,
                    task_prompt=args.task,
                    data_classification=timeline["data_handling"]["data_classification"],
                    allow_remote_processing=args.allow_remote_processing,
                )
            )
            fused = fuse_video_analysis(timeline, result)
            output = Path(args.output)
            write_json(output / "model-result.json", result.to_dict())
            write_json(output / "timeline.json", fused)
            _print_json(
                {
                    "ok": True,
                    "provider": result.provider,
                    "model_id": result.model_id,
                    "segments": len(result.analysis.get("segments", [])),
                    "timeline": str(output / "timeline.json"),
                }
            )
            return 0

        if args.command == "run-agent":
            if args.persona_count <= 0:
                raise ValueError("persona-count must be positive")
            if args.max_model_calls <= 0:
                raise ValueError("max-model-calls must be positive")
            timeline = read_json(args.timeline)
            validate_timeline(timeline)
            if not args.allow_remote_processing:
                raise PermissionError(
                    "allow-remote-processing 未确认；未把 Timeline 观察与 Persona 上下文发送给远程模型。"
                )
            if timeline["data_handling"]["data_classification"] not in {"public", "internal"}:
                raise PermissionError(
                    "Claude Code／Codex CLI 公有远程路由默认拒绝 confidential/restricted Timeline。"
                )
            event_count = sum(node["level"] == "event" for node in timeline["nodes"])
            call_plan = event_count * args.persona_count
            if call_plan > args.max_model_calls:
                raise ValueError(
                    f"model call plan is {call_plan}, above max-model-calls={args.max_model_calls}; "
                    "reduce persona-count or merge Timeline events"
                )
            pool_size = max(100, args.persona_count + 1)
            config = RunConfig(
                experiment_id=f"exp-model-{args.seed}",
                run_id=f"run-model-{args.seed}",
                seed=args.seed,
                pool_size=pool_size,
                deep_count=args.persona_count,
                sweep_count=1,
                projection_count=pool_size,
            )
            universe = SyntheticPersonaUniverse(pool_size, args.seed)
            if args.reasoner == "claude-code":
                reasoner = ClaudeCodeJsonReasoner(
                    model_id=args.model,
                    effort=args.effort,
                    max_budget_usd=args.max_budget_usd,
                )
                effective_budget = args.max_budget_usd
            else:
                reasoner = CodexCliJsonReasoner(
                    model_id=args.model,
                    effort=args.effort,
                )
                effective_budget = None
            traces = ModelSequentialRuntime(reasoner).run_deep(
                timeline,
                personas := universe.cohort(args.persona_count),
                config,
            )
            write_json(args.output, traces)
            manifest = build_sequential_run_manifest(
                timeline=timeline,
                personas=personas,
                traces=traces,
                config=config,
                runtime_mode="model_sequential",
                producer=ModelSequentialRuntime.producer,
                code_version=ModelSequentialRuntime.code_version,
                model_provider=reasoner.provider,
                model_id=reasoner.model_id,
                effort=args.effort,
                max_budget_usd=effective_budget,
            )
            manifest_path = Path(args.output).with_name("run-manifest.json")
            write_json(manifest_path, manifest)
            _print_json(
                {
                    "ok": True,
                    "traces": str(Path(args.output)),
                    "trace_events": len(traces),
                    "sessions": len({trace["session_id"] for trace in traces}),
                    "provider": reasoner.provider,
                    "model": reasoner.model_id,
                    "model_call_plan": call_plan,
                    "actual_model_calls": manifest["counts"]["actual_model_calls"],
                    "manifest": str(manifest_path),
                }
            )
            return 0

        if args.command == "calibrate":
            traces = read_json(args.traces)
            anchors_payload = read_json(args.anchors)
            anchors = anchors_payload.get("anchors", []) if isinstance(anchors_payload, dict) else anchors_payload
            if not isinstance(traces, list) or not isinstance(anchors, list):
                raise ValueError("traces and anchors must be JSON arrays")
            report = calibrate_traces(
                traces,
                anchors,
                top_k=args.top_k,
                agent_ab_direction=args.agent_ab_direction,
            )
            write_json(args.output, report)
            _print_json(report)
            return 0

        if args.command == "serve":
            from .webapp import run_server

            run_server(host=args.host, port=args.port, reload=args.reload)
            return 0
    except (
        ContractValidationError,
        FileNotFoundError,
        json.JSONDecodeError,
        PermissionError,
        RuntimeError,
        TimeoutError,
        ValueError,
    ) as exc:
        _print_json({"ok": False, "error": str(exc)})
        return 2

    parser.error("unsupported command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
