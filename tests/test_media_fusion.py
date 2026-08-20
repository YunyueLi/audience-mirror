from __future__ import annotations

import json
from pathlib import Path
import unittest

from audience_mirror.media.fusion import MAX_SEMANTIC_EVENTS, fuse_video_analysis
from audience_mirror.models.base import ModelUsage, VideoAnalysisResult
from audience_mirror.validation import validate_timeline


ROOT = Path(__file__).resolve().parents[1]


def _result(segments: list[dict[str, object]]) -> VideoAnalysisResult:
    return VideoAnalysisResult(
        provider="test-native-video",
        model_id="test-video-v1",
        analysis={"summary": "测试事实摘要", "segments": segments, "uncertainties": []},
        usage=ModelUsage(input_tokens=100, output_tokens=50, latency_ms=10),
    )


def _segment(start_ms: int, end_ms: int, index: int) -> dict[str, object]:
    return {
        "t_start_ms": start_ms,
        "t_end_ms": end_ms,
        "label": f"语义段 {index}",
        "summary": f"第 {index} 段可核查事实。",
        "observations": [
            {
                "modality": "multimodal",
                "kind": "narrative_event",
                "text": f"第 {index} 段发生了可见事件。",
                "confidence": 0.8,
            }
        ],
        "entity_refs": [f"entity-{index}"],
        "salience_tags": ["exposition"],
        "uncertainties": [],
    }


class MediaFusionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.timeline = json.loads(
            (ROOT / "fixtures" / "public-demo" / "timeline.json").read_text(encoding="utf-8")
        )

    def test_provider_segments_replace_sampling_events_and_keep_evidence(self) -> None:
        fused = fuse_video_analysis(
            self.timeline,
            _result([_segment(0, 120_000, 1), _segment(120_000, 240_000, 2)]),
        )
        events = [node for node in fused["nodes"] if node["level"] == "event"]
        self.assertEqual(len(events), 2)
        self.assertTrue(all(node["node_id"].startswith("event-semantic-") for node in events))
        self.assertTrue(all(node["observations"][0]["evidence_refs"] for node in events))
        self.assertTrue(all(node["review_status"] == "unreviewed" for node in events))
        self.assertEqual(fused["extensions"]["local_evidence_event_count"], 4)
        self.assertEqual(fused["extensions"]["semantic_event_count"], 2)
        validate_timeline(fused)

    def test_uncovered_spans_remain_explicit_instead_of_inventing_facts(self) -> None:
        fused = fuse_video_analysis(
            self.timeline,
            _result([_segment(10_000, 20_000, 1)]),
        )
        events = [node for node in fused["nodes"] if node["level"] == "event"]
        self.assertEqual([(node["t_start_ms"], node["t_end_ms"]) for node in events], [
            (0, 10_000),
            (10_000, 20_000),
            (20_000, 240_000),
        ])
        self.assertTrue(events[0]["extensions"]["coverage_gap"])
        self.assertEqual(events[0]["observations"][0]["epistemic_status"], "observed")
        self.assertIn("不补造", events[0]["summary"])
        validate_timeline(fused)

    def test_dense_provider_output_is_bounded_for_sequential_experience(self) -> None:
        segments = [
            _segment(index * 12_000, (index + 1) * 12_000, index + 1)
            for index in range(20)
        ]
        fused = fuse_video_analysis(self.timeline, _result(segments))
        events = [node for node in fused["nodes"] if node["level"] == "event"]
        self.assertLessEqual(len(events), MAX_SEMANTIC_EVENTS)
        self.assertEqual(events[0]["t_start_ms"], 0)
        self.assertEqual(events[-1]["t_end_ms"], 240_000)
        self.assertTrue(any("→" in node["label"] for node in events))
        validate_timeline(fused)


if __name__ == "__main__":
    unittest.main()
