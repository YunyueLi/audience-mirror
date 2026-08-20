from __future__ import annotations

import importlib.util
import math
import struct
import tempfile
import unittest
from pathlib import Path

from audience_mirror.media.ingest import VideoIngestConfig, ingest_video
from audience_mirror.validation import validate_timeline


@unittest.skipUnless(
    importlib.util.find_spec("av") and importlib.util.find_spec("PIL"),
    "media extra is not installed",
)
class RealVideoIngestTests(unittest.TestCase):
    def test_decodes_a_real_mp4_and_emits_frame_evidence(self) -> None:
        import av
        from PIL import Image

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "synthetic-public.mp4"
            container = av.open(str(source), mode="w")
            stream = container.add_stream("mpeg4", rate=2)
            stream.width = 160
            stream.height = 90
            stream.pix_fmt = "yuv420p"
            for color in ("#102a43", "#d64545", "#f0b429", "#2f855a"):
                frame = av.VideoFrame.from_image(Image.new("RGB", (160, 90), color=color))
                for packet in stream.encode(frame):
                    container.mux(packet)
            for packet in stream.encode():
                container.mux(packet)
            container.close()

            result = ingest_video(
                source,
                root / "artifacts",
                VideoIngestConfig(
                    sample_interval_ms=500,
                    scene_threshold=0.05,
                    max_frames=10,
                    extract_audio=False,
                ),
            )
            validate_timeline(result.timeline)
            self.assertGreaterEqual(len(result.manifest["frames"]), 2)
            self.assertTrue((root / "artifacts" / "timeline.json").is_file())
            self.assertTrue(result.timeline["extensions"]["local_ingest"])
            self.assertFalse(result.timeline["extensions"]["semantic_analysis_complete"])

    def test_extracts_a_real_audio_track_to_mono_wav(self) -> None:
        import av
        from PIL import Image

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "synthetic-public-with-audio.mp4"
            container = av.open(str(source), mode="w")
            video = container.add_stream("mpeg4", rate=10)
            video.width = 160
            video.height = 90
            video.pix_fmt = "yuv420p"
            audio = container.add_stream("aac", rate=16_000)
            audio.layout = "mono"
            for index in range(10):
                frame = av.VideoFrame.from_image(Image.new("RGB", (160, 90), color=(index * 20, 40, 110)))
                frame.pts = index
                for packet in video.encode(frame):
                    container.mux(packet)
            for packet in video.encode():
                container.mux(packet)
            sample_cursor = 0
            for _ in range(16):
                frame = av.AudioFrame(format="s16", layout="mono", samples=1024)
                frame.sample_rate = 16_000
                frame.pts = sample_cursor
                frame.planes[0].update(
                    b"".join(
                        struct.pack(
                            "<h",
                            int(8_000 * math.sin(2 * math.pi * 440 * (sample_cursor + offset) / 16_000)),
                        )
                        for offset in range(1024)
                    )
                )
                sample_cursor += 1024
                for packet in audio.encode(frame):
                    container.mux(packet)
            for packet in audio.encode():
                container.mux(packet)
            container.close()

            result = ingest_video(
                source,
                root / "artifacts",
                VideoIngestConfig(sample_interval_ms=500, scene_threshold=0.05),
            )
            extracted = result.manifest["audio"]
            self.assertIsNotNone(extracted)
            self.assertEqual(extracted["sample_rate"], 16_000)
            self.assertEqual(extracted["channels"], 1)
            self.assertGreaterEqual(extracted["duration_ms"], 900)
            self.assertTrue((root / "artifacts" / extracted["relative_path"]).is_file())
