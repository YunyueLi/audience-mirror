"""Generic Environment Contract and the first Timeline-backed media adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .hashing import fingerprint


ENVIRONMENT_SCHEMA_VERSION = "audience-mirror.environment/v0.1"


@dataclass(frozen=True, slots=True)
class Observation:
    observation_id: str
    step_index: int
    state_ref: str
    summary: str
    modalities: tuple[str, ...]
    evidence_refs: tuple[dict[str, Any], ...]
    terminal: bool = False
    extensions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "step_index": self.step_index,
            "state_ref": self.state_ref,
            "summary": self.summary,
            "modalities": list(self.modalities),
            "evidence_refs": list(self.evidence_refs),
            "terminal": self.terminal,
            "extensions": self.extensions,
        }


@dataclass(frozen=True, slots=True)
class Action:
    action_type: str
    parameters: dict[str, Any] = field(default_factory=dict)
    reason_summary: str | None = None


@dataclass(frozen=True, slots=True)
class Transition:
    observation: Observation
    accepted_action: Action
    reward_proxy: float | None = None
    info: dict[str, Any] = field(default_factory=dict)


class EnvironmentAdapter(Protocol):
    """Small runtime boundary shared by media, web, app, game and social environments."""

    @property
    def spec(self) -> dict[str, Any]: ...

    def reset(self, session_id: str) -> Observation: ...

    def step(self, session_id: str, action: Action) -> Transition: ...


def media_environment_spec(timeline: dict[str, Any], *, mode: str = "hybrid") -> dict[str, Any]:
    event_count = sum(1 for node in timeline["nodes"] if node["level"] == "event")
    config_material = {
        "timeline_id": timeline["timeline_id"],
        "timeline_hash": fingerprint(timeline),
        "mode": mode,
    }
    return {
        "schema_version": ENVIRONMENT_SCHEMA_VERSION,
        "environment_id": f"media:{timeline['timeline_id']}",
        "environment_type": "media",
        "version": "0.1.0",
        "asset_refs": [
            {
                "asset_id": timeline["asset"]["asset_id"],
                "variant_id": timeline["asset"]["variant_id"],
                "content_hash": timeline["asset"]["content_hash"],
                "object_ref": timeline["asset"].get("object_ref"),
            }
        ],
        "observation_space": {
            "modalities": ["multimodal", "visual", "speech", "music", "sound", "text"],
            "ordering": "sequential",
            "future_visibility": "blocked",
            "evidence_required": True,
        },
        "action_space": [
            {"action_type": "continue", "description": "继续体验下一个时间片。", "terminal": False},
            {"action_type": "pause", "description": "暂停并保留当前状态。", "terminal": False},
            {"action_type": "skip", "description": "跳过当前时间片。", "terminal": False},
            {"action_type": "rewind_requested", "description": "请求回看上一个时间片。", "terminal": False},
            {"action_type": "abandon", "description": "终止本次体验。", "terminal": True},
        ],
        "transition_policy": {
            "mode": mode,
            "terminal_actions": ["abandon"],
            "max_steps": max(event_count * 2, 1),
            "allow_revisit": True,
        },
        "data_handling": {
            "data_classification": timeline["data_handling"]["data_classification"],
            "export_policy": timeline["data_handling"]["export_policy"],
            "retention_class": timeline["data_handling"]["retention_class"],
        },
        "provenance": {
            "producer": "audience-mirror.timeline-media-environment",
            "code_version": "0.1.0",
            "config_hash": fingerprint(config_material),
        },
        "extensions": {
            "timeline_id": timeline["timeline_id"],
            "timeline_hash": fingerprint(timeline),
            "event_count": event_count,
        },
    }


def validate_environment_spec(spec: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "environment_id",
        "environment_type",
        "version",
        "observation_space",
        "action_space",
        "transition_policy",
        "data_handling",
        "provenance",
    }
    missing = sorted(required - set(spec))
    errors: list[str] = []
    if missing:
        errors.append(f"environment: missing fields {', '.join(missing)}")
    if spec.get("schema_version") != ENVIRONMENT_SCHEMA_VERSION:
        errors.append(f"environment.schema_version: expected {ENVIRONMENT_SCHEMA_VERSION!r}")
    actions = spec.get("action_space")
    if not isinstance(actions, list) or not actions:
        errors.append("environment.action_space: expected a non-empty list")
    elif len({item.get("action_type") for item in actions if isinstance(item, dict)}) != len(actions):
        errors.append("environment.action_space: action_type values must be unique")
    observation_space = spec.get("observation_space", {})
    if observation_space.get("future_visibility") not in {"blocked", "task_defined", "visible"}:
        errors.append("environment.observation_space.future_visibility: unsupported value")
    if errors:
        raise ValueError("\n".join(errors))


class TimelineMediaEnvironment:
    """A stateful, future-blind media Environment backed by event Timeline nodes."""

    def __init__(self, timeline: dict[str, Any]) -> None:
        self.timeline = timeline
        self._events = sorted(
            (node for node in timeline["nodes"] if node["level"] == "event"),
            key=lambda node: (node["t_start_ms"], node["node_id"]),
        )
        if not self._events:
            raise ValueError("TimelineMediaEnvironment requires at least one event node")
        self._sessions: dict[str, dict[str, Any]] = {}
        self._spec = media_environment_spec(timeline)
        validate_environment_spec(self._spec)

    @property
    def spec(self) -> dict[str, Any]:
        return self._spec

    def _observation(self, index: int, *, terminal: bool = False) -> Observation:
        bounded = min(max(index, 0), len(self._events) - 1)
        node = self._events[bounded]
        observations = node.get("observations", [])
        evidence = tuple(
            evidence_ref
            for item in observations
            for evidence_ref in item.get("evidence_refs", [])
        )
        modalities = tuple(dict.fromkeys(item.get("modality", "multimodal") for item in observations))
        summary = " ".join(item.get("text", "") for item in observations).strip() or node.get("summary") or node["label"]
        return Observation(
            observation_id=f"env-observation:{node['node_id']}:{index}",
            step_index=index,
            state_ref=node["node_id"],
            summary=summary,
            modalities=modalities or ("multimodal",),
            evidence_refs=evidence,
            terminal=terminal,
            extensions={
                "t_start_ms": node["t_start_ms"],
                "t_end_ms": node["t_end_ms"],
                "timeline_node": node,
            },
        )

    def reset(self, session_id: str) -> Observation:
        if not session_id:
            raise ValueError("session_id must not be empty")
        self._sessions[session_id] = {"index": 0, "terminal": False, "steps": 0}
        return self._observation(0)

    def step(self, session_id: str, action: Action) -> Transition:
        if session_id not in self._sessions:
            raise KeyError(f"unknown environment session {session_id!r}")
        state = self._sessions[session_id]
        if state["terminal"]:
            raise RuntimeError("cannot step a terminal environment session")
        allowed = {item["action_type"] for item in self._spec["action_space"]}
        if action.action_type not in allowed:
            raise ValueError(f"unsupported action_type {action.action_type!r}")

        previous_index = state["index"]
        if action.action_type == "rewind_requested":
            state["index"] = max(0, previous_index - 1)
        elif action.action_type in {"continue", "skip"}:
            state["index"] = min(previous_index + 1, len(self._events) - 1)
        elif action.action_type == "abandon":
            state["terminal"] = True
        state["steps"] += 1
        reached_end = previous_index == len(self._events) - 1 and action.action_type == "continue"
        if reached_end or state["steps"] >= self._spec["transition_policy"]["max_steps"]:
            state["terminal"] = True
        observation = self._observation(state["index"], terminal=state["terminal"])
        return Transition(
            observation=observation,
            accepted_action=action,
            info={
                "previous_step_index": previous_index,
                "current_step_index": state["index"],
                "terminal_reason": (
                    "abandon" if action.action_type == "abandon" else "completed" if reached_end else None
                ),
            },
        )
