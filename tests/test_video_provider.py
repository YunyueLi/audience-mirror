from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from audience_mirror.models.base import VideoAnalysisRequest
from audience_mirror.models.codex_frames import CodexFrameVideoProvider
from audience_mirror.models.gemini import GeminiVideoProvider


class GeminiVideoProviderGatesTests(unittest.TestCase):
    def _request(self, **overrides: object) -> VideoAnalysisRequest:
        values = {
            "video_path": Path("does-not-need-to-exist.mp4"),
            "asset_hash": "0" * 64,
            "duration_ms": 1_000,
            "data_classification": "public",
            "allow_remote_processing": False,
        }
        values.update(overrides)
        return VideoAnalysisRequest(**values)

    def test_remote_processing_is_denied_by_default(self) -> None:
        with self.assertRaisesRegex(PermissionError, "allow_remote_processing=false"):
            GeminiVideoProvider(api_key="unused").analyze(self._request())

    def test_public_adapter_rejects_confidential_assets(self) -> None:
        with self.assertRaisesRegex(PermissionError, "confidential/restricted"):
            GeminiVideoProvider(api_key="unused").analyze(
                self._request(
                    allow_remote_processing=True,
                    data_classification="confidential",
                )
            )


class CodexFrameVideoProviderTests(unittest.TestCase):
    def _request(self, root: Path, **overrides: object) -> VideoAnalysisRequest:
        frame_evidence = []
        for index, timestamp_ms in enumerate((0, 500, 1_000, 1_500), start=1):
            path = root / f"frame-{index}.jpg"
            path.write_bytes(f"frame-{index}".encode())
            frame_evidence.append({"path": str(path), "t_ms": timestamp_ms})
        values = {
            "video_path": root / "video.mp4",
            "asset_hash": "0" * 64,
            "duration_ms": 2_000,
            "data_classification": "public",
            "allow_remote_processing": True,
            "extensions": {"frame_evidence": frame_evidence},
        }
        values.update(overrides)
        return VideoAnalysisRequest(**values)

    def test_remote_processing_is_denied_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            request = self._request(Path(temporary_directory), allow_remote_processing=False)
            with self.assertRaisesRegex(PermissionError, "allow_remote_processing=false"):
                CodexFrameVideoProvider().analyze(request)

    def test_cli_receives_bounded_images_and_discloses_frame_baseline(self) -> None:
        analysis = {
            "summary": "可见画面摘要",
            "segments": [
                {
                    "t_start_ms": 0,
                    "t_end_ms": 2_000,
                    "label": "画面变化",
                    "summary": "画面由一变为二",
                    "observations": [
                        {"modality": "visual", "kind": "frame_comparison", "text": "画面变化", "confidence": 0.7}
                    ],
                    "entity_refs": [],
                    "salience_tags": [],
                    "uncertainties": ["帧间过程不可见"],
                }
            ],
            "uncertainties": ["没有音轨"],
        }

        def fake_run(command, **kwargs):
            output = Path(command[command.index("--output-last-message") + 1])
            output.write_text(json.dumps(analysis, ensure_ascii=False), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as temporary_directory:
            request = self._request(Path(temporary_directory))
            with patch("audience_mirror.models.codex_frames.subprocess.run", side_effect=fake_run) as run:
                result = CodexFrameVideoProvider(max_images=3).analyze(request)
        command = run.call_args.args[0]
        image_flag = command.index("--image")
        model_flag = command.index("--model")
        self.assertEqual(len(command[image_flag + 1 : model_flag]), 3)
        self.assertIn("--ephemeral", command)
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertIn("未发送原视频或音轨", result.warnings[0])
        self.assertEqual(result.analysis["summary"], "可见画面摘要")

    def test_frame_budget_is_distributed_by_time_not_scene_frame_density(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            timestamps = [0, 10, 20, 30, 40, 500, 750, 1_000]
            frame_evidence = []
            for index, timestamp_ms in enumerate(timestamps):
                path = root / f"dense-{index}.jpg"
                path.write_bytes(b"frame")
                frame_evidence.append({"path": str(path), "t_ms": timestamp_ms})
            request = VideoAnalysisRequest(
                video_path=root / "video.mp4",
                asset_hash="0" * 64,
                duration_ms=1_000,
                allow_remote_processing=True,
                extensions={"frame_evidence": frame_evidence},
            )
            selected = CodexFrameVideoProvider(max_images=3)._selected_frames(request)
        self.assertEqual([frame["t_ms"] for frame in selected], [0, 500, 1_000])
