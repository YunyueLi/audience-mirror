"""Model-driven, future-blind sequential experience runtime."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import json
from typing import Any

from .domain import Persona, RunConfig
from .hashing import event_fingerprint, fingerprint
from .reasoning import JsonReasoner
from .runtime import DeterministicMediaRuntime
from .validation import validate_trace_stream


REACTIONS = {
    "understanding",
    "confusion",
    "surprise",
    "delight",
    "frustration",
    "boredom",
    "trust_change",
    "character_affinity_change",
    "memory_formed",
    "share_language",
    "purchase_objection",
    "other",
}
ACTIONS = {
    "continue",
    "pause_marked",
    "rewind_requested",
    "skip",
    "abandon",
    "share_considered",
    "payment_considered",
    "none",
}
STATE_KEYS = {
    "attention_proxy",
    "valence",
    "arousal",
    "comprehension",
    "confusion",
    "trust",
    "continue_intent",
    "share_intent",
    "consider_paying",
    "uncertainty",
}


AGENT_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "state_after",
        "reaction_type",
        "reaction_summary",
        "decision_basis_summary",
        "confidence",
        "action_type",
        "action_reason",
        "memory_summary",
        "perceived_facts",
        "open_questions",
    ],
    "properties": {
        "state_after": {
            "type": "object",
            "additionalProperties": False,
            "required": sorted(STATE_KEYS),
            "properties": {
                **{
                    key: {"type": "number", "minimum": 0, "maximum": 1}
                    for key in STATE_KEYS - {"valence"}
                },
                "valence": {"type": "number", "minimum": -1, "maximum": 1},
            },
        },
        "reaction_type": {"type": "string", "enum": sorted(REACTIONS)},
        "reaction_summary": {"type": "string", "maxLength": 800},
        "decision_basis_summary": {"type": "string", "maxLength": 800},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "action_type": {"type": "string", "enum": sorted(ACTIONS)},
        "action_reason": {"type": "string", "maxLength": 600},
        "memory_summary": {"type": "string", "maxLength": 800},
        "perceived_facts": {"type": "array", "items": {"type": "string", "maxLength": 500}},
        "open_questions": {"type": "array", "items": {"type": "string", "maxLength": 500}},
    },
}


def _normalized_state(previous: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    state = deepcopy(previous)
    for key in STATE_KEYS:
        value = raw.get(key, previous[key])
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            value = previous[key]
        low = -1.0 if key == "valence" else 0.0
        state[key] = round(min(max(float(value), low), 1.0), 4)
    state["character_affinity"] = deepcopy(previous.get("character_affinity", {}))
    state["expectations"] = list(previous.get("expectations", []))[-3:]
    return state


def _event_and_status(action: str, *, is_first: bool, is_last: bool) -> tuple[str, str, str]:
    before = "ready" if is_first else "watching"
    if action == "abandon":
        return "action.abandon", before, "abandoned"
    if action == "skip":
        return "action.skip", before, "skipped_window"
    if action == "rewind_requested":
        return "action.rewind_requested", before, "review_marked"
    if action == "pause_marked":
        return "action.pause_marked", before, "review_marked"
    if action == "share_considered":
        return "action.share_considered", before, "watching"
    if action == "payment_considered":
        return "action.payment_considered", before, "watching"
    if is_last:
        return "session.completed", before, "completed"
    return "state.updated", before, "watching"


class ModelSequentialRuntime:
    """Runs one structured model call per Persona and observed Timeline event."""

    producer = "audience-mirror.model-sequential-runtime"
    code_version = "0.2.0"

    def __init__(self, reasoner: JsonReasoner) -> None:
        self.reasoner = reasoner

    def _prompt(
        self,
        *,
        persona: Persona,
        node: dict[str, Any],
        previous_state: dict[str, Any],
        memories: list[str],
        sequence_no: int,
        total_events: int,
    ) -> str:
        current_observations = [
            {
                "modality": observation["modality"],
                "kind": observation["kind"],
                "text": observation["text"],
                "epistemic_status": observation["epistemic_status"],
                "confidence": observation["confidence"],
            }
            for observation in node.get("observations", [])
        ]
        payload = {
            "persona": persona.to_dict(),
            "experience_progress": {"current_index": sequence_no, "known_total_events": total_events},
            "current_environment_state": {
                "timeline_node_id": node["node_id"],
                "t_start_ms": node["t_start_ms"],
                "t_end_ms": node["t_end_ms"],
                "label": node["label"],
                "summary": node.get("summary"),
                "observations": current_observations,
            },
            "previous_state": previous_state,
            "episodic_memory": memories[-5:],
            "allowed_actions": ["continue", "pause_marked", "rewind_requested", "skip", "abandon"],
        }
        return (
            "你正在执行 Audience Mirror 的独立、顺序体验实验。请稳定扮演给定 Persona，只能使用当前事件与此前记忆；"
            "绝不能推断或引用未来事件、片名外部知识、发布后口碑或市场结果。attention、emotion、purchase 等均为预测代理量。"
            "输出可展示的简短依据，不输出隐藏思维链。根据 JSON Schema 返回完整对象。\n\n"
            + json.dumps(payload, ensure_ascii=False, sort_keys=True)
        )

    def run_deep(
        self,
        timeline: dict[str, Any],
        personas: list[Persona],
        config: RunConfig,
    ) -> list[dict[str, Any]]:
        template_personas = [
            Persona(
                persona_id=persona.persona_id,
                segment_id=persona.segment_id,
                familiarity=1.0,
                narrative_patience=1.0,
                novelty_preference=persona.novelty_preference,
                price_sensitivity=persona.price_sensitivity,
                attention_context="focused_viewing",
                source=persona.source,
                uncertainty=persona.uncertainty,
            )
            for persona in personas
        ]
        baseline = DeterministicMediaRuntime().run_deep(timeline, template_personas, config)
        by_agent: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for trace in baseline:
            by_agent[trace["agent_id"]].append(trace)
        nodes = {node["node_id"]: node for node in timeline["nodes"]}
        output: list[dict[str, Any]] = []
        persona_by_id = {persona.persona_id: persona for persona in personas}

        for agent_id, templates in by_agent.items():
            persona = persona_by_id[agent_id]
            ordered = sorted(templates, key=lambda item: item["session_sequence_no"])
            previous_state = deepcopy(ordered[0]["state"]["before"])
            memories: list[str] = []
            previous_trace_id: str | None = None
            previous_event_hash: str | None = None
            for sequence_no, template in enumerate(ordered):
                node = nodes[template["timeline"]["timeline_node_id"]]
                prompt = self._prompt(
                    persona=persona,
                    node=node,
                    previous_state=previous_state,
                    memories=memories,
                    sequence_no=sequence_no,
                    total_events=len(ordered),
                )
                reasoning = self.reasoner.respond_json(prompt, AGENT_RESPONSE_SCHEMA)
                value = reasoning.value
                action = value.get("action_type") if value.get("action_type") in ACTIONS else "continue"
                state_after = _normalized_state(previous_state, value.get("state_after", {}))
                memory_summary = str(value.get("memory_summary") or value.get("reaction_summary") or node["label"])[:800]
                memories.append(memory_summary)
                trace = deepcopy(template)
                trace["previous_trace_event_id"] = previous_trace_id
                trace["previous_event_hash"] = previous_event_hash
                trace["stream_version"] = sequence_no + 1
                event_type, status_before, status_after = _event_and_status(
                    action, is_first=sequence_no == 0, is_last=sequence_no == len(ordered) - 1
                )
                trace["event_type"] = event_type
                trace["state"] = {
                    "session_status_before": status_before,
                    "session_status_after": status_after,
                    "before": previous_state,
                    "after": state_after,
                }
                trace["observation"] = {
                    "summary": " ".join(item["text"] for item in node.get("observations", []))[:2000],
                    "perceived_facts": [str(item)[:1000] for item in value.get("perceived_facts", [])],
                    "open_questions": [str(item)[:1000] for item in value.get("open_questions", [])],
                    "epistemic_status": "inferred",
                }
                reaction_type = value.get("reaction_type") if value.get("reaction_type") in REACTIONS else "other"
                trace["reaction"] = {
                    "reaction_type": reaction_type,
                    "summary": str(value.get("reaction_summary") or "未返回反应摘要。")[:1500],
                    "decision_basis_summary": str(
                        value.get("decision_basis_summary") or "依据当前可见事件、Persona 与此前记忆。"
                    )[:1500],
                    "confidence": round(min(max(float(value.get("confidence", 0.5)), 0.0), 1.0), 4),
                }
                trace["action"] = {
                    "action_type": action,
                    "target_segment_id": node["node_id"],
                    "reason_summary": str(value.get("action_reason") or "模型未返回动作依据。")[:1000],
                }
                memory_id = f"memory-{persona.persona_id}-{sequence_no:03d}"
                trace["memory"] = {
                    "reads": [f"memory-{persona.persona_id}-{index:03d}" for index in range(sequence_no)],
                    "writes": [
                        {
                            "memory_id": memory_id,
                            "memory_type": "episodic",
                            "summary": memory_summary,
                            "source_trace_event_ids": [trace["trace_event_id"]],
                            "confidence": trace["reaction"]["confidence"],
                            "data_classification": timeline["data_handling"]["data_classification"],
                            "export_policy": timeline["data_handling"]["export_policy"],
                            "redaction_status": timeline["data_handling"]["redaction_status"],
                        }
                    ],
                    "working_memory_hash": fingerprint(memories[-3:]),
                    "long_term_memory_hash": fingerprint(memories),
                }
                trace["provenance"] = {
                    "provenance_type": "model",
                    "producer": self.producer,
                    "code_version": self.code_version,
                    "experiment_manifest_hash": fingerprint(config.to_dict()),
                    "cache_key": fingerprint(
                        {"prompt": prompt, "provider": reasoning.provider, "model": reasoning.model_id}
                    ),
                    "persona_snapshot_hash": persona.snapshot_hash,
                    "prompt_hash": fingerprint(prompt),
                    "model_provider": reasoning.provider,
                    "model_id": reasoning.model_id,
                    "model_version": reasoning.model_version,
                    "random_seed": config.seed,
                    "region": "local-cli" if "cli" in reasoning.provider else None,
                    "actor_ref": None,
                }
                trace["cost"] = {
                    "latency_ms": max(reasoning.latency_ms, 0),
                    "input_tokens": max(reasoning.input_tokens, 0),
                    "output_tokens": max(reasoning.output_tokens, 0),
                    "media_tokens": 0,
                    "currency": "USD",
                    "estimated_cost": reasoning.estimated_cost_usd,
                    "cache_hit": False,
                }
                trace["extensions"] = {
                    "fixture_only": False,
                    "model_driven": True,
                    "future_visibility": "blocked",
                    "statistical_representativeness": False,
                    "proxy_measurements": True,
                }
                trace["event_hash"] = event_fingerprint(trace)
                output.append(trace)
                previous_state = state_after
                previous_trace_id = trace["trace_event_id"]
                previous_event_hash = trace["event_hash"]
                if action == "abandon":
                    break

        validate_trace_stream(output, timeline)
        return output
