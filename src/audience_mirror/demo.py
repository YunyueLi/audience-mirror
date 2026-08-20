"""End-to-end deterministic public demo orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .adapters.matraix import MatrAixAdapter
from .domain import RunConfig
from .hashing import fingerprint
from .io import file_sha256, read_json, write_json, write_text
from .report import build_report
from .runtime import DeterministicMediaRuntime
from .universe import SEGMENTS, SyntheticPersonaUniverse
from .validation import timeline_hash, validate_timeline


def run_public_demo(
    *,
    timeline_path: str | Path,
    output_directory: str | Path,
    config: RunConfig,
) -> dict[str, Any]:
    timeline_source = Path(timeline_path)
    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)

    timeline = read_json(timeline_source)
    validate_timeline(timeline)
    universe = SyntheticPersonaUniverse(config.pool_size, config.seed)
    deep_personas = universe.cohort(config.deep_count)
    sweep_personas = universe.cohort(config.sweep_count, offset=config.deep_count)
    runtime = DeterministicMediaRuntime()

    traces = runtime.run_deep(timeline, deep_personas, config)
    sweep = runtime.run_sweep(timeline, sweep_personas, config)
    projection = runtime.project_population(timeline, universe, config.projection_count)
    matraix_contract = MatrAixAdapter().build_media_task_contract(
        timeline=timeline,
        personas=deep_personas,
        config=config,
    )

    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    files = {
        "timeline": output / "timeline.json",
        "personas": output / "deep-personas.json",
        "deep_traces": output / "deep-traces.json",
        "broad_sweep": output / "broad-sweep.json",
        "projection": output / "population-projection.json",
        "matraix_contract": output / "matraix-media-contract.json",
    }
    write_json(files["timeline"], timeline)
    write_json(files["personas"], [persona.to_dict() for persona in deep_personas])
    write_json(files["deep_traces"], traces)
    write_json(files["broad_sweep"], sweep)
    write_json(files["projection"], projection)
    write_json(files["matraix_contract"], matraix_contract)

    manifest = {
        "schema_version": "audience-mirror.run-manifest/v0.1",
        "experiment_id": config.experiment_id,
        "run_id": config.run_id,
        "generated_at": generated_at,
        "seed": config.seed,
        "timeline_hash": timeline_hash(timeline),
        "persona_universe_hash": fingerprint(
            {
                "type": "synthetic_fixture",
                "size": config.pool_size,
                "seed": config.seed,
                "segments": SEGMENTS,
            }
        ),
        "counts": {
            "persona_pool_records": config.pool_size,
            "deep_personas": len(deep_personas),
            "deep_trace_events": len(traces),
            "broad_sweep_runs": len(sweep),
            "projected_records": projection["projected_records"],
            "stability_runs": 1,
            "human_participants": 0,
        },
        "runtime": {
            "producer": runtime.producer,
            "version": runtime.code_version,
            "mode": "deterministic_fixture",
        },
        "cost": {
            "model_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0,
        },
        "calibration_status": "uncalibrated",
        "statistical_representativeness": False,
        "reception_context": {
            "condition": "independent_blind",
            "information_cutoff": None,
            "information_cutoff_basis": "synthetic_fixture_no_external_information",
            "outcome_blinded": True,
            "context_seed_sha256": None,
        },
        "data_policy": {
            "contains_private_media": False,
            "contains_personal_data": False,
            "contains_third_party_persona_data": False,
            "fixture_only": True,
        },
        "files": {
            key: {
                "path": path.name,
                "sha256": file_sha256(path),
            }
            for key, path in files.items()
        },
        "limitations": [
            "All media events and personas are synthetic fixtures.",
            "Proxy values are deterministic engineering outputs, not human predictions.",
            "Broad Sweep is not a complete viewing session.",
            "Population Projection performs zero per-persona LLM calls and is not a human sample.",
            "No human calibration data is present.",
            "The run tests independent blind reception only; no social-context scenario is executed.",
        ],
    }
    manifest_path = output / "run-manifest.json"
    write_json(manifest_path, manifest)
    report = build_report(
        timeline=timeline,
        personas=deep_personas,
        traces=traces,
        sweep=sweep,
        projection=projection,
        manifest=manifest,
    )
    report_path = output / "report.html"
    write_text(report_path, report)

    return {
        "ok": True,
        "output_directory": str(output.resolve()),
        "report": str(report_path.resolve()),
        "manifest": str(manifest_path.resolve()),
        "counts": manifest["counts"],
        "model_calls": 0,
        "estimated_cost_usd": 0,
    }
