from __future__ import annotations

import unittest
from pathlib import Path

from audience_mirror.models.base import VideoAnalysisRequest
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
