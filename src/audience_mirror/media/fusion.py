"""Fuse provider-derived video segments into the evidence-preserving Timeline."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
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


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _bounded_time(value: Any, duration_ms: int, default: int) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    return min(max(int(value), 0), duration_ms)


def _overlap(start_a: int, end_a: int, start_b: int, end_b: int) -> int:
    return max(0, min(end_a, end_b) - max(start_a, start_b))


def fuse_video_analysis(timeline: dict[str, Any], result: VideoAnalysisResult) -> dict[str, Any]:
    fused = deepcopy(timeline)
    duration_ms = int(fused["duration_ms"])
    event_nodes = [node for node in fused["nodes"] if node["level"] == "event"]
    if not event_nodes:
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
    segments = result.analysis.get("segments", [])
    for segment_index, raw_segment in enumerate(segments):
        if not isinstance(raw_segment, dict):
            continue
        start_ms = _bounded_time(raw_segment.get("t_start_ms"), duration_ms, 0)
        end_ms = _bounded_time(raw_segment.get("t_end_ms"), duration_ms, min(duration_ms, start_ms + 1))
        if end_ms <= start_ms:
            end_ms = min(duration_ms, start_ms + 1)
        target = max(
            event_nodes,
            key=lambda node: (
                _overlap(start_ms, end_ms, node["t_start_ms"], node["t_end_ms"]),
                -abs(node["t_start_ms"] - start_ms),
            ),
        )
        evidence_refs = deepcopy(target["observations"][0]["evidence_refs"])
        raw_observations = raw_segment.get("observations")
        if not isinstance(raw_observations, list) or not raw_observations:
            raw_observations = [
                {
                    "modality": "multimodal",
                    "kind": "segment_summary",
                    "text": raw_segment.get("summary") or raw_segment.get("label") or "模型未返回段落摘要。",
                    "confidence": 0.5,
                }
            ]
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
            target["observations"].append(
                {
                    "observation_id": f"observation-model-{segment_index + 1:04d}-{observation_index + 1:02d}",
                    "modality": modality,
                    "kind": str(raw_observation.get("kind") or "provider_observation")[:120],
                    "text": text[:3000],
                    "epistemic_status": "inferred",
                    "confidence": round(min(max(float(confidence), 0.0), 1.0), 4),
                    "evidence_refs": evidence_refs,
                    "producer_ref": extractor_run_id,
                }
            )
        if raw_segment.get("label"):
            target["label"] = str(raw_segment["label"])[:300]
        if raw_segment.get("summary"):
            target["summary"] = str(raw_segment["summary"])[:3000]
        target["entity_refs"] = list(
            dict.fromkeys(
                target.get("entity_refs", [])
                + [str(value) for value in raw_segment.get("entity_refs", []) if value]
            )
        )
        target["salience_tags"] = list(
            dict.fromkeys(
                target.get("salience_tags", [])
                + [value for value in raw_segment.get("salience_tags", []) if value in ALLOWED_SALIENCE]
            )
        )
        target["extensions"]["provider_segment"] = {
            "t_start_ms": start_ms,
            "t_end_ms": end_ms,
            "uncertainties": raw_segment.get("uncertainties", []),
        }
    fused["extensions"]["semantic_analysis_complete"] = True
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
