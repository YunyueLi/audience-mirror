"""Fuse provider-derived video segments into the evidence-preserving Timeline."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from math import ceil
from typing import Any

from ..hashing import fingerprint, sha256_text
from ..models.base import VideoAnalysisResult
from ..validation import validate_timeline


ALLOWED_MODALITIES = {"visual", "speech", "text", "music", "sound", "multimodal"}
ALLOWED_SALIENCE = {
    "exposition",
    "character_change",
    "relationship_change",
    "goal_change",
    "reveal",
    "conflict",
    "payoff",
    "visual_spectacle",
    "music_change",
    "silence",
    "ui_change",
    "purchase_exposure",
    "share_hook",
    "safety_critical",
}
MAX_SEMANTIC_EVENTS = 16


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _bounded_time(value: Any, duration_ms: int, default: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    return min(max(int(value), 0), duration_ms)


def _overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> int:
    return max(0, min(end_a, end_b) - max(start_a, start_b))


def _evidence_in_window(
    event_nodes: list[dict[str, Any]],
    start_ms: int,
    end_ms: int,
) -> list[dict[str, Any]]:
    """Collect stable frame/audio references for a semantic time window."""

    candidates: list[tuple[int, dict[str, Any]]] = []
    seen: set[str] = set()
    for node in event_nodes:
        for observation in node.get("observations", []):
            for evidence in observation.get("evidence_refs", []):
                evidence_start = int(evidence.get("t_start_ms", node["t_start_ms"]))
                evidence_end = int(evidence.get("t_end_ms", evidence_start))
                intersects = evidence_end >= start_ms and evidence_start <= end_ms
                if not intersects:
                    continue
                ref_id = str(evidence.get("ref_id") or "")
                if ref_id in seen:
                    continue
                seen.add(ref_id)
                candidates.append((evidence_start, deepcopy(evidence)))
    if candidates:
        return [evidence for _, evidence in sorted(candidates, key=lambda item: item[0])]

    # A provider boundary may fall between sparse local samples. Use the nearest
    # local evidence point and disclose that approximation in node extensions.
    nearest: tuple[int, dict[str, Any]] | None = None
    midpoint = (start_ms + end_ms) // 2
    for node in event_nodes:
        for observation in node.get("observations", []):
            for evidence in observation.get("evidence_refs", []):
                timestamp = int(evidence.get("t_start_ms", node["t_start_ms"]))
                distance = abs(timestamp - midpoint)
                if nearest is None or distance < nearest[0]:
                    nearest = (distance, deepcopy(evidence))
    return [nearest[1]] if nearest else []


def _normalized_segments(analysis: dict[str, Any], duration_ms: int) -> list[dict[str, Any]]:
    raw_segments: list[dict[str, Any]] = []
    for raw in analysis.get("segments", []):
        if not isinstance(raw, dict):
            continue
        start_ms = _bounded_time(raw.get("t_start_ms"), duration_ms, 0)
        end_ms = _bounded_time(raw.get("t_end_ms"), duration_ms, min(duration_ms, start_ms + 1))
        if end_ms <= start_ms:
            continue
        raw_segments.append({**deepcopy(raw), "t_start_ms": start_ms, "t_end_ms": end_ms})
    raw_segments.sort(key=lambda item: (item["t_start_ms"], item["t_end_ms"]))
    if not raw_segments:
        raise ValueError("video model returned no valid semantic segments")

    # Build complete, non-overlapping coverage. Missing provider spans remain
    # explicit gaps instead of being silently attributed to a neighbouring fact.
    covered: list[dict[str, Any]] = []
    cursor = 0
    for raw in raw_segments:
        start_ms = max(cursor, int(raw["t_start_ms"]))
        end_ms = int(raw["t_end_ms"])
        if start_ms > cursor:
            covered.append(
                {
                    "t_start_ms": cursor,
                    "t_end_ms": start_ms,
                    "label": "未解释时间窗",
                    "summary": "多模态 Provider 未返回这一时间窗的语义；仅保留本地证据，不补造内容事实。",
                    "observations": [],
                    "entity_refs": [],
                    "salience_tags": [],
                    "uncertainties": ["provider_coverage_gap"],
                    "coverage_gap": True,
                }
            )
        if end_ms <= start_ms:
            continue
        raw["t_start_ms"] = start_ms
        raw["t_end_ms"] = end_ms
        raw["coverage_gap"] = False
        covered.append(raw)
        cursor = end_ms
        if cursor >= duration_ms:
            break
    if cursor < duration_ms:
        covered.append(
            {
                "t_start_ms": cursor,
                "t_end_ms": duration_ms,
                "label": "未解释时间窗",
                "summary": "多模态 Provider 未返回这一时间窗的语义；仅保留本地证据，不补造内容事实。",
                "observations": [],
                "entity_refs": [],
                "salience_tags": [],
                "uncertainties": ["provider_coverage_gap"],
                "coverage_gap": True,
            }
        )
    return covered


def _coalesce_segments(
    segments: list[dict[str, Any]],
    max_events: int = MAX_SEMANTIC_EVENTS,
) -> list[dict[str, Any]]:
    if len(segments) <= max_events:
        return segments
    chunk_size = ceil(len(segments) / max_events)
    compacted: list[dict[str, Any]] = []
    for offset in range(0, len(segments), chunk_size):
        group = segments[offset : offset + chunk_size]
        labels = [str(item.get("label") or "语义事件") for item in group]
        summaries = [str(item.get("summary") or "") for item in group if item.get("summary")]
        compacted.append(
            {
                "t_start_ms": group[0]["t_start_ms"],
                "t_end_ms": group[-1]["t_end_ms"],
                "label": labels[0] if len(group) == 1 else f"{labels[0]} → {labels[-1]}",
                "summary": " ".join(summaries)[:3000] or "合并的连续语义时间窗。",
                "observations": [
                    deepcopy(observation)
                    for item in group
                    for observation in item.get("observations", [])
                    if isinstance(observation, dict)
                ],
                "entity_refs": list(
                    dict.fromkeys(
                        str(value)
                        for item in group
                        for value in item.get("entity_refs", [])
                        if value
                    )
                ),
                "salience_tags": list(
                    dict.fromkeys(
                        value
                        for item in group
                        for value in item.get("salience_tags", [])
                        if value in ALLOWED_SALIENCE
                    )
                ),
                "uncertainties": list(
                    dict.fromkeys(
                        str(value)
                        for item in group
                        for value in item.get("uncertainties", [])
                        if value
                    )
                ),
                "coverage_gap": all(bool(item.get("coverage_gap")) for item in group),
                "source_windows": [
                    {
                        "t_start_ms": item["t_start_ms"],
                        "t_end_ms": item["t_end_ms"],
                        "coverage_gap": bool(item.get("coverage_gap")),
                    }
                    for item in group
                ],
            }
        )
    return compacted


def _containing_parent(
    structural_nodes: list[dict[str, Any]],
    start_ms: int,
    end_ms: int,
) -> str | None:
    candidates = [
        node
        for node in structural_nodes
        if node["t_start_ms"] <= start_ms and node["t_end_ms"] >= end_ms
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda node: node["t_end_ms"] - node["t_start_ms"])["node_id"]


def fuse_video_analysis(timeline: dict[str, Any], result: VideoAnalysisResult) -> dict[str, Any]:
    fused = deepcopy(timeline)
    duration_ms = int(fused["duration_ms"])
    original_events = [node for node in fused["nodes"] if node["level"] == "event"]
    structural_nodes = [node for node in fused["nodes"] if node["level"] != "event"]
    if not original_events:
        raise ValueError("timeline has no event nodes to receive provider analysis")
    extractor_run_id = f"extract-{result.provider}-{fingerprint(result.analysis)[:12]}"
    fused["extractor_manifest"].append(
        {
            "extractor_run_id": extractor_run_id,
            "capability": "vision_caption",
            "producer": result.provider,
            "model_id": result.model_id,
            "version": "0.1.0",
            "config_hash": fingerprint(
                {"provider": result.provider, "model_id": result.model_id, "analysis": result.analysis}
            ),
            "ran_at": _utc_now(),
        }
    )
    segments = _coalesce_segments(_normalized_segments(result.analysis, duration_ms))
    semantic_events: list[dict[str, Any]] = []
    local_producer_ref = next(
        (
            observation.get("producer_ref")
            for node in original_events
            for observation in node.get("observations", [])
            if observation.get("producer_ref")
        ),
        None,
    )
    for segment_index, raw_segment in enumerate(segments):
        start_ms = int(raw_segment["t_start_ms"])
        end_ms = int(raw_segment["t_end_ms"])
        evidence_refs = _evidence_in_window(original_events, start_ms, end_ms)
        if not evidence_refs:
            raise ValueError("semantic segment has no local evidence reference")
        raw_observations = raw_segment.get("observations")
        if not isinstance(raw_observations, list) or not raw_observations:
            raw_observations = [
                {
                    "modality": "visual",
                    "kind": "local_evidence_window" if raw_segment.get("coverage_gap") else "segment_summary",
                    "text": raw_segment.get("summary") or raw_segment.get("label") or "模型未返回段落摘要。",
                    "confidence": 1.0 if raw_segment.get("coverage_gap") else 0.5,
                }
            ]
        observations: list[dict[str, Any]] = []
        for observation_index, raw_observation in enumerate(raw_observations):
            if not isinstance(raw_observation, dict):
                continue
            modality = raw_observation.get("modality", "multimodal")
            if modality not in ALLOWED_MODALITIES:
                modality = "multimodal"
            confidence = raw_observation.get("confidence", 0.5)
            if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
                confidence = 0.5
            text = str(raw_observation.get("text") or raw_segment.get("summary") or "未返回文本").strip()
            coverage_gap = bool(raw_segment.get("coverage_gap"))
            observations.append(
                {
                    "observation_id": f"observation-model-{segment_index + 1:04d}-{observation_index + 1:02d}",
                    "modality": modality,
                    "kind": str(raw_observation.get("kind") or "provider_observation")[:120],
                    "text": text[:3000],
                    "epistemic_status": "observed" if coverage_gap else "inferred",
                    "confidence": round(min(max(float(confidence), 0.0), 1.0), 4),
                    "evidence_refs": deepcopy(evidence_refs),
                    "producer_ref": local_producer_ref if coverage_gap else extractor_run_id,
                }
            )
        semantic_events.append(
            {
                "node_id": f"event-semantic-{segment_index + 1:04d}",
                "parent_node_id": _containing_parent(structural_nodes, start_ms, end_ms),
                "level": "event",
                "t_start_ms": start_ms,
                "t_end_ms": end_ms,
                "label": str(raw_segment.get("label") or f"语义事件 {segment_index + 1}")[:300],
                "summary": str(raw_segment.get("summary") or "模型未返回段落摘要。")[:3000],
                "observations": observations,
                "entity_refs": list(
                    dict.fromkeys(str(value) for value in raw_segment.get("entity_refs", []) if value)
                ),
                "salience_tags": list(
                    dict.fromkeys(
                        value for value in raw_segment.get("salience_tags", []) if value in ALLOWED_SALIENCE
                    )
                ),
                "review_status": "unreviewed",
                "review_notes": "多模态模型生成；须回到时间点和本地证据复核。",
                "extensions": {
                    "provider_segment": {
                        "t_start_ms": start_ms,
                        "t_end_ms": end_ms,
                        "uncertainties": raw_segment.get("uncertainties", []),
                    },
                    "coverage_gap": bool(raw_segment.get("coverage_gap")),
                    "source_windows": raw_segment.get(
                        "source_windows",
                        [{"t_start_ms": start_ms, "t_end_ms": end_ms, "coverage_gap": False}],
                    ),
                    "evidence_ref_count": len(evidence_refs),
                },
            }
        )
    fused["nodes"] = structural_nodes + semantic_events
    fused["extensions"]["semantic_analysis_complete"] = True
    fused["extensions"]["semantic_event_count"] = len(semantic_events)
    fused["extensions"]["local_evidence_event_count"] = len(original_events)
    fused["extensions"]["semantic_event_budget"] = MAX_SEMANTIC_EVENTS
    fused["extensions"]["video_model"] = {
        "provider": result.provider,
        "model_id": result.model_id,
        "analysis_hash": fingerprint(result.analysis),
        "usage": result.usage.to_dict(),
        "warnings": list(result.warnings),
        "summary_hash": sha256_text(str(result.analysis.get("summary", ""))),
    }
    validate_timeline(fused)
    return fused
