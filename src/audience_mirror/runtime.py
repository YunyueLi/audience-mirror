"""Deterministic local runtime for Deep Trace, Broad Sweep and Projection.

This module is an executable contract baseline, not a human-behavior model.
Every output explicitly records that it is a synthetic fixture and uses zero
LLM calls.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from .domain import Persona, RunConfig
from .hashing import event_fingerprint, fingerprint, sha256_text
from .universe import SEGMENTS, SyntheticPersonaUniverse
from .validation import timeline_hash, validate_trace_stream


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _unit_noise(*parts: str) -> float:
    digest = sha256_text("::".join(parts))
    integer = int(digest[:12], 16)
    return integer / float(0xFFFFFFFFFFFF)


def _initial_state(persona: Persona) -> dict[str, Any]:
    return {
        "attention_proxy": round(0.48 + 0.35 * persona.narrative_patience, 4),
        "valence": 0.0,
        "arousal": 0.25,
        "comprehension": round(0.35 + 0.35 * persona.familiarity, 4),
        "confusion": round(0.5 - 0.25 * persona.familiarity, 4),
        "trust": 0.5,
        "continue_intent": round(0.45 + 0.4 * persona.narrative_patience, 4),
        "share_intent": 0.2,
        "consider_paying": round(0.25 * (1 - persona.price_sensitivity), 4),
        "uncertainty": 0.7,
        "character_affinity": {},
        "expectations": [],
    }


def _next_state(
    previous: dict[str, Any], persona: Persona, node: dict[str, Any]
) -> dict[str, Any]:
    signals = node.get("extensions", {}).get("fixture_signals", {})
    clarity = float(signals.get("clarity", 0.65))
    pace = float(signals.get("pace", 0.55))
    emotional_intensity = float(signals.get("emotional_intensity", 0.45))
    novelty = float(signals.get("novelty", 0.5))
    valence_signal = float(signals.get("valence", 0.0))
    noise = _unit_noise(persona.persona_id, node["node_id"])
    attention_penalty = 0.1 if persona.attention_context == "mobile_with_interruptions" else 0.0

    comprehension = _clamp(
        0.4 * previous["comprehension"]
        + 0.38 * clarity
        + 0.12 * persona.familiarity
        + 0.1 * noise
    )
    confusion = _clamp(0.72 * (1 - comprehension) + 0.18 * (1 - clarity) + 0.1 * (1 - noise))
    attention = _clamp(
        0.32 * previous["attention_proxy"]
        + 0.25 * pace
        + 0.2 * emotional_intensity
        + 0.15 * (novelty * persona.novelty_preference)
        + 0.08 * noise
        - attention_penalty
    )
    continue_intent = _clamp(
        0.42 * previous["continue_intent"]
        + 0.25 * persona.narrative_patience
        + 0.2 * attention
        + 0.13 * comprehension
        - 0.16 * confusion
    )
    share_intent = _clamp(0.2 * previous["share_intent"] + 0.38 * novelty + 0.3 * emotional_intensity + 0.12 * noise)
    paying = _clamp(
        0.4 * previous["consider_paying"]
        + 0.28 * comprehension
        + 0.2 * max(valence_signal, 0)
        + 0.12 * continue_intent
        - 0.25 * persona.price_sensitivity
    )
    return {
        "attention_proxy": round(attention, 4),
        "valence": round(max(-1.0, min(1.0, 0.45 * previous["valence"] + 0.55 * valence_signal)), 4),
        "arousal": round(_clamp(0.3 * previous["arousal"] + 0.7 * emotional_intensity), 4),
        "comprehension": round(comprehension, 4),
        "confusion": round(confusion, 4),
        "trust": round(_clamp(0.55 * previous["trust"] + 0.3 * clarity + 0.15 * comprehension), 4),
        "continue_intent": round(continue_intent, 4),
        "share_intent": round(share_intent, 4),
        "consider_paying": round(paying, 4),
        "uncertainty": round(_clamp(0.55 * previous["uncertainty"] + 0.45 * (1 - clarity)), 4),
        "character_affinity": deepcopy(previous.get("character_affinity", {})),
        "expectations": [node.get("summary") or node["label"]][-3:],
    }


def _reaction(after: dict[str, Any]) -> tuple[str, str]:
    if after["confusion"] >= 0.58:
        return "confusion", "信息关系仍不清楚，后续判断保持较高不确定性。"
    if after["arousal"] >= 0.68 and after["valence"] >= 0.15:
        return "delight", "情绪强度和正向效价同时上升。"
    if after["arousal"] >= 0.68:
        return "surprise", "当前事件提高了唤醒代理量，但方向尚未稳定。"
    if after["attention_proxy"] <= 0.35:
        return "boredom", "注意代理量下降，继续观看意向受到影响。"
    return "understanding", "当前事件被纳入既有理解，未出现强烈冲突。"


def _action(after: dict[str, Any]) -> tuple[str, str]:
    if after["continue_intent"] < 0.16:
        return "abandon", "继续意向低于合成 Fixture 的放弃阈值。"
    if after["continue_intent"] < 0.3:
        return "skip", "继续意向较低，标记跳过风险。"
    if after["confusion"] > 0.64:
        return "rewind_requested", "困惑代理量较高，标记回看需求。"
    return "continue", "继续观看。"


class DeterministicMediaRuntime:
    producer = "audience-mirror.deterministic-media-runtime"
    code_version = "0.1.0"

    def run_deep(
        self,
        timeline: dict[str, Any],
        personas: list[Persona],
        config: RunConfig,
    ) -> list[dict[str, Any]]:
        timeline_digest = timeline_hash(timeline)
        event_nodes = sorted(
            (node for node in timeline["nodes"] if node["level"] == "event"),
            key=lambda node: (node["t_start_ms"], node["node_id"]),
        )
        if not event_nodes:
            raise ValueError("the local runtime requires at least one event-level Timeline node")

        traces: list[dict[str, Any]] = []
        experiment_manifest_hash = fingerprint(config.to_dict())
        observed_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        for persona in personas:
            previous_state = _initial_state(persona)
            previous_trace_id: str | None = None
            previous_event_hash: str | None = None
            memory_summaries: list[str] = []
            session_id = f"session-{config.run_id}-{persona.persona_id}"

            for sequence_no, node in enumerate(event_nodes):
                after = _next_state(previous_state, persona, node)
                reaction_type, reaction_summary = _reaction(after)
                action_type, action_reason = _action(after)
                is_last = sequence_no == len(event_nodes) - 1
                status_before = "ready" if sequence_no == 0 else "watching"
                if action_type == "abandon":
                    status_after = "abandoned"
                    event_type = "action.abandon"
                elif is_last:
                    status_after = "completed"
                    event_type = "session.completed"
                elif action_type == "skip":
                    status_after = "skipped_window"
                    event_type = "action.skip"
                else:
                    status_after = "watching"
                    event_type = "state.updated"

                observation = node["observations"][0]
                evidence = observation["evidence_refs"][0]
                trace_event_id = f"trace-{config.run_id}-{persona.persona_id}-{sequence_no:03d}"
                memory_summary = f"{node['label']}：{reaction_summary}"
                memory_summaries.append(memory_summary)
                trace = {
                    "schema_version": "audience-mirror.trace/v0.1",
                    "trace_event_id": trace_event_id,
                    "session_sequence_no": sequence_no,
                    "idempotency_key": fingerprint(
                        {"session_id": session_id, "sequence_no": sequence_no, "node_id": node["node_id"]}
                    ),
                    "stream_version": sequence_no + 1,
                    "previous_trace_event_id": previous_trace_id,
                    "previous_event_hash": previous_event_hash,
                    "event_hash": "0" * 64,
                    "experiment_id": config.experiment_id,
                    "run_id": config.run_id,
                    "run_type": "independent_sequential",
                    "session_id": session_id,
                    "agent_id": persona.persona_id,
                    "segment_id": persona.segment_id,
                    "asset": deepcopy(timeline["asset"]),
                    "data_handling": deepcopy(timeline["data_handling"]),
                    "timeline": {
                        "timeline_id": timeline["timeline_id"],
                        "timeline_schema_version": timeline["schema_version"],
                        "timeline_hash": timeline_digest,
                        "timeline_node_id": node["node_id"],
                        "t_start_ms": node["t_start_ms"],
                        "t_end_ms": node["t_end_ms"],
                        "exposure_index": sequence_no,
                    },
                    "event_type": event_type,
                    "observed_at": observed_at,
                    "state": {
                        "session_status_before": status_before,
                        "session_status_after": status_after,
                        "before": previous_state,
                        "after": after,
                    },
                    "observation": {
                        "summary": observation["text"],
                        "perceived_facts": [observation["text"]],
                        "open_questions": ["该反应是否能在同任务真人记录中复现？"],
                        "epistemic_status": "observed",
                    },
                    "reaction": {
                        "reaction_type": reaction_type,
                        "summary": reaction_summary,
                        "decision_basis_summary": "依据当前 Timeline 事件、合成 Persona 特征和此前状态计算。",
                        "confidence": round(1 - after["uncertainty"], 4),
                    },
                    "action": {
                        "action_type": action_type,
                        "target_segment_id": node["node_id"],
                        "reason_summary": action_reason,
                    },
                    "evidence": [
                        {
                            "ref_id": f"trace-evidence-{evidence['ref_id']}",
                            "evidence_type": "timeline_observation",
                            "timeline_observation_id": observation["observation_id"],
                            "t_start_ms": evidence["t_start_ms"],
                            "t_end_ms": evidence["t_end_ms"],
                            "object_ref": evidence.get("object_ref"),
                            "hash_algorithm": "sha256",
                            "content_hash": evidence["content_hash"],
                            "data_classification": evidence["data_classification"],
                            "export_policy": evidence["export_policy"],
                            "redaction_status": evidence["redaction_status"],
                            "excerpt": evidence.get("excerpt"),
                        }
                    ],
                    "memory": {
                        "reads": [f"memory-{persona.persona_id}-{index:03d}" for index in range(sequence_no)],
                        "writes": [
                            {
                                "memory_id": f"memory-{persona.persona_id}-{sequence_no:03d}",
                                "memory_type": "episodic",
                                "summary": memory_summary,
                                "source_trace_event_ids": [trace_event_id],
                                "confidence": round(1 - after["uncertainty"], 4),
                                "data_classification": "public",
                                "export_policy": "authorized",
                                "redaction_status": "not_required",
                            }
                        ],
                        "working_memory_hash": fingerprint(memory_summaries[-3:]),
                        "long_term_memory_hash": fingerprint(memory_summaries),
                    },
                    "provenance": {
                        "provenance_type": "system",
                        "producer": self.producer,
                        "code_version": self.code_version,
                        "experiment_manifest_hash": experiment_manifest_hash,
                        "cache_key": fingerprint(
                            {"timeline": timeline_digest, "persona": persona.snapshot_hash, "node": node["node_id"]}
                        ),
                        "persona_snapshot_hash": persona.snapshot_hash,
                        "prompt_hash": None,
                        "model_provider": None,
                        "model_id": "deterministic-fixture",
                        "model_version": self.code_version,
                        "random_seed": config.seed,
                        "region": "local",
                        "actor_ref": None,
                    },
                    "cost": {
                        "latency_ms": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "media_tokens": 0,
                        "currency": "USD",
                        "estimated_cost": 0,
                        "cache_hit": True,
                    },
                    "calibration": None,
                    "review": None,
                    "social": None,
                    "extensions": {
                        "fixture_only": True,
                        "statistical_representativeness": False,
                    },
                }
                trace["event_hash"] = event_fingerprint(trace)
                traces.append(trace)
                previous_state = after
                previous_trace_id = trace_event_id
                previous_event_hash = trace["event_hash"]
                if action_type == "abandon":
                    break

        validate_trace_stream(traces, timeline)
        return traces

    def run_sweep(
        self,
        timeline: dict[str, Any],
        personas: list[Persona],
        config: RunConfig,
    ) -> list[dict[str, Any]]:
        event_nodes = [node for node in timeline["nodes"] if node["level"] == "event"]
        mean_clarity = sum(
            float(node.get("extensions", {}).get("fixture_signals", {}).get("clarity", 0.65))
            for node in event_nodes
        ) / len(event_nodes)
        results: list[dict[str, Any]] = []
        for persona in personas:
            noise = _unit_noise(config.run_id, "sweep", persona.persona_id)
            comprehension = _clamp(0.5 * mean_clarity + 0.32 * persona.familiarity + 0.18 * noise)
            continue_intent = _clamp(0.5 * comprehension + 0.34 * persona.narrative_patience + 0.16 * noise)
            risk = "high" if continue_intent < 0.35 else "medium" if continue_intent < 0.62 else "low"
            results.append(
                {
                    "persona_id": persona.persona_id,
                    "segment_id": persona.segment_id,
                    "run_type": "broad_sweep",
                    "completed_experience": False,
                    "input_scope": "frozen_timeline_summary",
                    "comprehension_proxy": round(comprehension, 4),
                    "continue_intent_proxy": round(continue_intent, 4),
                    "dropoff_risk_band": risk,
                    "reason_summary": "基于冻结 Timeline 摘要的结构化合成 Fixture；不是完整观看。",
                    "model_calls": 0,
                    "estimated_cost_usd": 0,
                }
            )
        return results

    def project_population(
        self,
        timeline: dict[str, Any],
        universe: SyntheticPersonaUniverse,
        count: int,
    ) -> dict[str, Any]:
        event_nodes = [node for node in timeline["nodes"] if node["level"] == "event"]
        mean_clarity = sum(
            float(node.get("extensions", {}).get("fixture_signals", {}).get("clarity", 0.65))
            for node in event_nodes
        ) / len(event_nodes)
        cells: Counter[tuple[str, str]] = Counter()
        for index in range(count):
            persona = universe.persona_at(index)
            score = _clamp(0.52 * mean_clarity + 0.3 * persona.familiarity + 0.18 * persona.narrative_patience)
            band = "high" if score < 0.4 else "medium" if score < 0.64 else "low"
            cells[(persona.segment_id, band)] += 1

        rows = [
            {
                "segment_id": segment,
                "projected_records": sum(cells[(segment, band)] for band in ("low", "medium", "high")),
                "low_risk": cells[(segment, "low")],
                "medium_risk": cells[(segment, "medium")],
                "high_risk": cells[(segment, "high")],
            }
            for segment in SEGMENTS
        ]
        return {
            "projection_mode": "rule_based_fixture",
            "projected_records": count,
            "llm_calls": 0,
            "completed_experiences": 0,
            "statistical_representativeness": False,
            "calibration_status": "uncalibrated",
            "rows": rows,
            "limitations": [
                "Projection records are not independent viewing sessions.",
                "The synthetic Persona Universe is not calibrated to a real population.",
                "Risk bands are engineering fixtures and must not be used as market forecasts.",
            ],
        }
