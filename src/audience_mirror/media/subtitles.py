"""Parse platform WebVTT captions and attach them to semantic Timeline events."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
import re
from typing import Any

from ..hashing import fingerprint
from ..validation import validate_timeline


_TIMING_LINE = re.compile(
    r"^(?P<start>(?:\d{1,3}:)?\d{2}:\d{2}[.,]\d{3})\s+-->\s+"
    r"(?P<end>(?:\d{1,3}:)?\d{2}:\d{2}[.,]\d{3})(?:\s+.*)?$"
)
_VTT_TAG = re.compile(r"<[^>]+>")
MAX_CUES_PER_EVENT = 24


@dataclass(frozen=True, slots=True)
class SubtitleCue:
    index: int
    t_start_ms: int
    t_end_ms: int
    text: str


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _timestamp_ms(value: str) -> int:
    fields = value.replace(",", ".").split(":")
    if len(fields) == 2:
        hours = 0
        minutes, seconds = fields
    elif len(fields) == 3:
        hours, minutes, seconds = fields
    else:
        raise ValueError(f"invalid WebVTT timestamp: {value}")
    return int(hours) * 3_600_000 + int(minutes) * 60_000 + int(float(seconds) * 1000)


def _clean_caption_text(lines: list[str]) -> str:
    values: list[str] = []
    for line in lines:
        cleaned = unescape(_VTT_TAG.sub("", line)).replace("\u200b", "").strip()
        if cleaned and (not values or cleaned != values[-1]):
            values.append(cleaned)
    return " ".join(values).strip()


def parse_webvtt(value: str) -> list[SubtitleCue]:
    """Parse the useful timing/text subset of WebVTT without a runtime dependency."""

    normalized = value.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    blocks = re.split(r"\n\s*\n", normalized)
    cues: list[SubtitleCue] = []
    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines or lines[0].startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue
        timing_index = next((index for index, line in enumerate(lines[:2]) if "-->" in line), None)
        if timing_index is None:
            continue
        match = _TIMING_LINE.match(lines[timing_index])
        if match is None:
            continue
        start_ms = _timestamp_ms(match.group("start"))
        end_ms = _timestamp_ms(match.group("end"))
        text = _clean_caption_text(lines[timing_index + 1 :])
        if end_ms <= start_ms or not text:
            continue
        cues.append(
            SubtitleCue(
                index=len(cues) + 1,
                t_start_ms=start_ms,
                t_end_ms=end_ms,
                text=text,
            )
        )
    return cues


def attach_webvtt_subtitles(
    timeline: dict[str, Any],
    subtitle_path: str | Path,
    subtitle_metadata: dict[str, Any],
) -> dict[str, Any]:
    """Attach a bounded subtitle observation to each overlapping event.

    The observation records what the platform caption track says. It does not
    assert speaker identity, transcript accuracy, or that every caption is
    verbatim dialogue.
    """

    path = Path(subtitle_path).resolve()
    cues = parse_webvtt(path.read_text(encoding="utf-8-sig"))
    if not cues:
        return deepcopy(timeline)
    content_hash = str(subtitle_metadata.get("content_hash") or "")
    if not re.fullmatch(r"[a-fA-F0-9]{64}", content_hash):
        raise ValueError("subtitle metadata requires a sha256 content_hash")
    fused = deepcopy(timeline)
    language = str(subtitle_metadata.get("language") or "und")[:80]
    producer_ref = f"extract-platform-subtitle-{content_hash[:12]}"
    fused["extractor_manifest"].append(
        {
            "extractor_run_id": producer_ref,
            "capability": "timeline_fusion",
            "producer": "audience-mirror.platform-subtitle",
            "model_id": None,
            "version": "0.1.0",
            "config_hash": fingerprint(
                {
                    "content_hash": content_hash,
                    "language": language,
                    "max_cues_per_event": MAX_CUES_PER_EVENT,
                }
            ),
            "ran_at": _utc_now(),
        }
    )
    handling = fused["data_handling"]
    attached_events = 0
    for node_index, node in enumerate(fused["nodes"]):
        if node.get("level") != "event":
            continue
        overlapping = [
            cue
            for cue in cues
            if cue.t_end_ms > int(node["t_start_ms"])
            and cue.t_start_ms < int(node["t_end_ms"])
        ]
        if not overlapping:
            continue
        selected = overlapping[:MAX_CUES_PER_EVENT]
        evidence_refs = [
            {
                "ref_id": f"evidence-subtitle-{content_hash[:12]}-{cue.index:04d}",
                "evidence_type": "subtitle",
                "t_start_ms": cue.t_start_ms,
                "t_end_ms": cue.t_end_ms,
                "object_ref": f"subtitle:{content_hash[:16]}:{cue.index:04d}",
                "hash_algorithm": "sha256",
                "content_hash": content_hash,
                "data_classification": handling["data_classification"],
                "export_policy": handling["export_policy"],
                "redaction_status": handling["redaction_status"],
                "excerpt": cue.text[:500],
            }
            for cue in selected
        ]
        caption_text = "\n".join(cue.text for cue in selected)[:3000]
        node["observations"].append(
            {
                "observation_id": f"observation-subtitle-{node_index + 1:04d}",
                "modality": "text",
                "kind": "platform_subtitle",
                "text": caption_text,
                "epistemic_status": "observed",
                "confidence": 0.9,
                "evidence_refs": evidence_refs,
                "producer_ref": producer_ref,
            }
        )
        node.setdefault("extensions", {})["subtitle"] = {
            "language": language,
            "source_type": str(subtitle_metadata.get("source_type") or "platform_caption"),
            "machine_generated": bool(subtitle_metadata.get("machine_generated", False)),
            "cues_total": len(overlapping),
            "cues_attached": len(selected),
            "truncated": len(selected) < len(overlapping),
        }
        attached_events += 1
    fused.setdefault("extensions", {})["subtitle_track"] = {
        "language": language,
        "source_type": str(subtitle_metadata.get("source_type") or "platform_caption"),
        "machine_generated": bool(subtitle_metadata.get("machine_generated", False)),
        "cue_count": len(cues),
        "attached_event_count": attached_events,
        "content_hash": content_hash,
        "limitations": [
            "平台字幕未在本原型中核对说话人、逐字准确度或与声音的完整一致性。"
        ],
    }
    validate_timeline(fused)
    return fused
