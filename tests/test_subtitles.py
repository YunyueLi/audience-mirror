from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from audience_mirror.io import read_json
from audience_mirror.media.subtitles import attach_webvtt_subtitles, parse_webvtt
from audience_mirror.validation import validate_timeline


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class SubtitleTimelineTests(unittest.TestCase):
    def test_webvtt_parser_handles_identifiers_tags_and_settings(self) -> None:
        cues = parse_webvtt(
            """WEBVTT

cue-1
00:00:01.000 --> 00:00:03.250 position:50%
<v Sintel>Hello &amp; welcome</v>

00:04.000 --> 00:05.500
Second line
"""
        )
        self.assertEqual(len(cues), 2)
        self.assertEqual((cues[0].t_start_ms, cues[0].t_end_ms), (1000, 3250))
        self.assertEqual(cues[0].text, "Hello & welcome")
        self.assertEqual(cues[1].text, "Second line")

    def test_manual_caption_cues_are_attached_as_bounded_evidence(self) -> None:
        timeline = read_json(REPOSITORY_ROOT / "fixtures" / "public-demo" / "timeline.json")
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "zh-Hans.vtt"
            path.write_text(
                """WEBVTT

00:00:01.000 --> 00:00:03.000
第一段对白

00:02:10.000 --> 00:02:13.000
后半段对白
""",
                encoding="utf-8",
            )
            fused = attach_webvtt_subtitles(
                timeline,
                path,
                {
                    "language": "zh-Hans",
                    "source_type": "platform_manual_caption",
                    "machine_generated": False,
                    "content_hash": "a" * 64,
                },
            )
        validate_timeline(fused)
        subtitle_observations = [
            observation
            for node in fused["nodes"]
            if node["level"] == "event"
            for observation in node["observations"]
            if observation["kind"] == "platform_subtitle"
        ]
        self.assertEqual(len(subtitle_observations), 2)
        self.assertEqual(subtitle_observations[0]["modality"], "text")
        self.assertEqual(
            subtitle_observations[0]["evidence_refs"][0]["evidence_type"],
            "subtitle",
        )
        self.assertNotIn(str(path), str(fused))
        self.assertEqual(fused["extensions"]["subtitle_track"]["cue_count"], 2)


if __name__ == "__main__":
    unittest.main()
