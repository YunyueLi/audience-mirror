"""Repository-level validation for Timeline and Trace contracts.

The baseline deliberately has no runtime dependencies. It validates the invariants that
matter for experiment trust and keeps the canonical JSON Schemas as the public contract.
Projects that already use ``jsonschema`` may additionally validate the same payloads
against ``schemas/*.schema.json``.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any, Iterable

from .hashing import event_fingerprint, fingerprint
from .resources import resource_path


SCHEMA_DIRECTORY = resource_path("schemas")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class ContractValidationError(ValueError):
    """Raised when one or more contract or semantic checks fail."""

    def __init__(self, errors: Iterable[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("\n".join(self.errors))


def load_schema(schema_name: str) -> dict[str, Any]:
    path = SCHEMA_DIRECTORY / schema_name
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _require_keys(payload: dict[str, Any], required: Iterable[str], context: str) -> list[str]:
    return [f"{context}: missing required field {key!r}" for key in required if key not in payload]


def _validate_sha256(value: Any, context: str) -> list[str]:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        return [f"{context}: expected a 64-character SHA-256 hex digest"]
    return []


def validate_timeline(timeline: dict[str, Any]) -> None:
    schema = load_schema("timeline.schema.json")
    errors = _require_keys(timeline, schema["required"], "timeline")
    expected_version = schema["properties"]["schema_version"]["const"]
    if timeline.get("schema_version") != expected_version:
        errors.append(f"timeline.schema_version: expected {expected_version!r}")

    asset = timeline.get("asset")
    if not isinstance(asset, dict):
        errors.append("timeline.asset: expected an object")
    else:
        errors.extend(_require_keys(asset, schema["$defs"]["assetRef"]["required"], "timeline.asset"))
        errors.extend(_validate_sha256(asset.get("content_hash"), "timeline.asset.content_hash"))

    duration_ms = timeline.get("duration_ms")
    if not isinstance(duration_ms, int) or duration_ms <= 0:
        errors.append("timeline.duration_ms: expected a positive integer")

    nodes = timeline.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        errors.append("timeline.nodes: expected a non-empty list")
        if errors:
            raise ContractValidationError(errors)
        return

    node_required = schema["$defs"]["timelineNode"]["required"]
    observation_required = schema["$defs"]["observation"]["required"]
    evidence_required = schema["$defs"]["evidenceRef"]["required"]
    allowed_levels = set(schema["$defs"]["timelineNode"]["properties"]["level"]["enum"])
    allowed_review = set(schema["$defs"]["timelineNode"]["properties"]["review_status"]["enum"])
    extractor_ids = {
        item.get("extractor_run_id")
        for item in timeline.get("extractor_manifest", [])
        if isinstance(item, dict)
    }

    by_id: dict[str, dict[str, Any]] = {}
    observation_ids: set[str] = set()
    for index, node in enumerate(nodes):
        context = f"timeline.nodes[{index}]"
        if not isinstance(node, dict):
            errors.append(f"{context}: expected an object")
            continue
        errors.extend(_require_keys(node, node_required, context))
        node_id = node.get("node_id")
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"{context}.node_id: expected a non-empty string")
        elif node_id in by_id:
            errors.append(f"{context}.node_id: duplicate node_id {node_id!r}")
        else:
            by_id[node_id] = node

        start = node.get("t_start_ms")
        end = node.get("t_end_ms")
        if not isinstance(start, int) or not isinstance(end, int) or end <= start:
            errors.append(f"{context}: expected integer t_end_ms > t_start_ms")
        elif isinstance(duration_ms, int) and (start < 0 or end > duration_ms):
            errors.append(f"{context}: node time range is outside the asset duration")
        if node.get("level") not in allowed_levels:
            errors.append(f"{context}.level: unsupported level {node.get('level')!r}")
        if node.get("review_status") not in allowed_review:
            errors.append(f"{context}.review_status: unsupported status")

        observations = node.get("observations")
        if not isinstance(observations, list):
            errors.append(f"{context}.observations: expected a list")
            continue
        for observation_index, observation in enumerate(observations):
            observation_context = f"{context}.observations[{observation_index}]"
            if not isinstance(observation, dict):
                errors.append(f"{observation_context}: expected an object")
                continue
            errors.extend(_require_keys(observation, observation_required, observation_context))
            observation_id = observation.get("observation_id")
            if not isinstance(observation_id, str) or not observation_id:
                errors.append(f"{observation_context}.observation_id: expected a non-empty string")
            elif observation_id in observation_ids:
                errors.append(f"{observation_context}.observation_id: duplicate observation id")
            else:
                observation_ids.add(observation_id)
            producer_ref = observation.get("producer_ref")
            if producer_ref is not None and producer_ref not in extractor_ids:
                errors.append(f"{observation_context}.producer_ref: unknown extractor {producer_ref!r}")
            confidence = observation.get("confidence")
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                errors.append(f"{observation_context}.confidence: expected a value from 0 to 1")
            evidence_refs = observation.get("evidence_refs")
            if not isinstance(evidence_refs, list) or not evidence_refs:
                errors.append(f"{observation_context}.evidence_refs: expected a non-empty list")
                continue
            for evidence_index, evidence in enumerate(evidence_refs):
                evidence_context = f"{observation_context}.evidence_refs[{evidence_index}]"
                if not isinstance(evidence, dict):
                    errors.append(f"{evidence_context}: expected an object")
                    continue
                errors.extend(_require_keys(evidence, evidence_required, evidence_context))
                errors.extend(_validate_sha256(evidence.get("content_hash"), f"{evidence_context}.content_hash"))
                evidence_start = evidence.get("t_start_ms")
                evidence_end = evidence.get("t_end_ms")
                if (
                    not isinstance(evidence_start, int)
                    or not isinstance(evidence_end, int)
                    or evidence_end < evidence_start
                ):
                    errors.append(f"{evidence_context}: invalid evidence time range")
                elif isinstance(duration_ms, int) and (evidence_start < 0 or evidence_end > duration_ms):
                    errors.append(f"{evidence_context}: evidence is outside the asset duration")

    for node_id, node in by_id.items():
        parent_id = node.get("parent_node_id")
        if parent_id is None:
            continue
        parent = by_id.get(parent_id)
        if parent is None:
            errors.append(f"timeline node {node_id!r}: unknown parent {parent_id!r}")
            continue
        if node["t_start_ms"] < parent["t_start_ms"] or node["t_end_ms"] > parent["t_end_ms"]:
            errors.append(f"timeline node {node_id!r}: child time range is not contained by its parent")

    for start_id in by_id:
        seen: set[str] = set()
        current_id: str | None = start_id
        while current_id is not None:
            if current_id in seen:
                errors.append(f"timeline node {start_id!r}: parent hierarchy contains a cycle")
                break
            seen.add(current_id)
            current = by_id.get(current_id)
            if current is None:
                break
            current_id = current.get("parent_node_id")

    if errors:
        raise ContractValidationError(errors)


def timeline_hash(timeline: dict[str, Any]) -> str:
    validate_timeline(timeline)
    return fingerprint(timeline)


def validate_trace_stream(traces: list[dict[str, Any]], timeline: dict[str, Any]) -> None:
    validate_timeline(timeline)
    schema = load_schema("trace.schema.json")
    errors: list[str] = []
    expected_version = schema["properties"]["schema_version"]["const"]
    required = schema["required"]
    required_evidence = schema["$defs"]["evidenceRef"]["required"]
    required_state = schema["$defs"]["stateTransition"]["required"]
    required_memory = schema["$defs"]["memoryDelta"]["required"]
    required_provenance = schema["$defs"]["provenance"]["required"]
    expected_timeline_hash = fingerprint(timeline)
    timeline_nodes = {node["node_id"]: node for node in timeline["nodes"]}
    observation_ids = {
        observation["observation_id"]
        for node in timeline["nodes"]
        for observation in node["observations"]
    }

    sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for index, trace in enumerate(traces):
        context = f"traces[{index}]"
        if not isinstance(trace, dict):
            errors.append(f"{context}: expected an object")
            continue
        errors.extend(_require_keys(trace, required, context))
        if trace.get("schema_version") != expected_version:
            errors.append(f"{context}.schema_version: expected {expected_version!r}")
        errors.extend(_validate_sha256(trace.get("event_hash"), f"{context}.event_hash"))
        if isinstance(trace.get("event_hash"), str) and trace.get("event_hash") != event_fingerprint(trace):
            errors.append(f"{context}.event_hash: does not match the canonical event payload")

        trace_asset = trace.get("asset")
        if not isinstance(trace_asset, dict) or trace_asset.get("content_hash") != timeline["asset"]["content_hash"]:
            errors.append(f"{context}.asset: does not match the Timeline asset")
        timeline_ref = trace.get("timeline")
        if not isinstance(timeline_ref, dict):
            errors.append(f"{context}.timeline: expected an object")
        else:
            if timeline_ref.get("timeline_hash") != expected_timeline_hash:
                errors.append(f"{context}.timeline.timeline_hash: does not match the supplied Timeline")
            node = timeline_nodes.get(timeline_ref.get("timeline_node_id"))
            if node is None:
                errors.append(f"{context}.timeline.timeline_node_id: unknown node")
            elif (
                timeline_ref.get("t_start_ms") != node["t_start_ms"]
                or timeline_ref.get("t_end_ms") != node["t_end_ms"]
            ):
                errors.append(f"{context}.timeline: time range does not match its node")

        state = trace.get("state")
        if not isinstance(state, dict):
            errors.append(f"{context}.state: expected an object")
        else:
            errors.extend(_require_keys(state, required_state, f"{context}.state"))
        memory = trace.get("memory")
        if not isinstance(memory, dict):
            errors.append(f"{context}.memory: expected an object")
        else:
            errors.extend(_require_keys(memory, required_memory, f"{context}.memory"))
        provenance = trace.get("provenance")
        if not isinstance(provenance, dict):
            errors.append(f"{context}.provenance: expected an object")
        else:
            errors.extend(_require_keys(provenance, required_provenance, f"{context}.provenance"))

        evidence_items = trace.get("evidence")
        if not isinstance(evidence_items, list):
            errors.append(f"{context}.evidence: expected a list")
        else:
            for evidence_index, evidence in enumerate(evidence_items):
                evidence_context = f"{context}.evidence[{evidence_index}]"
                if not isinstance(evidence, dict):
                    errors.append(f"{evidence_context}: expected an object")
                    continue
                errors.extend(_require_keys(evidence, required_evidence, evidence_context))
                if evidence.get("timeline_observation_id") not in observation_ids:
                    errors.append(f"{evidence_context}.timeline_observation_id: unknown observation")
                errors.extend(_validate_sha256(evidence.get("content_hash"), f"{evidence_context}.content_hash"))

        session_id = trace.get("session_id")
        if isinstance(session_id, str):
            sessions[session_id].append(trace)

    for session_id, session_traces in sessions.items():
        ordered = sorted(session_traces, key=lambda item: item.get("session_sequence_no", -1))
        previous_id: str | None = None
        previous_hash: str | None = None
        previous_exposure = -1
        for expected_sequence, trace in enumerate(ordered):
            if trace.get("session_sequence_no") != expected_sequence:
                errors.append(f"session {session_id!r}: non-contiguous session_sequence_no")
            if trace.get("stream_version") != expected_sequence + 1:
                errors.append(f"session {session_id!r}: stream_version must increase from 1")
            if trace.get("previous_trace_event_id") != previous_id:
                errors.append(f"session {session_id!r}: previous_trace_event_id chain is broken")
            if trace.get("previous_event_hash") != previous_hash:
                errors.append(f"session {session_id!r}: previous_event_hash chain is broken")
            exposure_index = trace.get("timeline", {}).get("exposure_index", -1)
            if not isinstance(exposure_index, int) or exposure_index <= previous_exposure:
                errors.append(f"session {session_id!r}: exposure_index must strictly increase")
            previous_id = trace.get("trace_event_id")
            previous_hash = trace.get("event_hash")
            previous_exposure = exposure_index

    if errors:
        raise ContractValidationError(errors)
