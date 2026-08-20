from __future__ import annotations

from email.message import Message
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from audience_mirror.media.source import (
    _DownloadBudget,
    SourceImportError,
    _assert_public_destination,
    _choose_platform_subtitle,
    _choose_platform_formats,
    _validated_platform_duration_seconds,
    classify_video_url,
    import_video_url,
)


class _FakeResponse:
    def __init__(self, payload: bytes, content_type: str = "video/mp4") -> None:
        self._payload = payload
        self._read = False
        self.closed = False
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self.headers["Content-Length"] = str(len(payload))

    def read(self, size: int = -1) -> bytes:
        if self._read:
            return b""
        self._read = True
        return self._payload

    def close(self) -> None:
        self.closed = True


class MediaSourceTests(unittest.TestCase):
    def test_platform_subtitle_prefers_manual_chinese_webvtt(self) -> None:
        selected = _choose_platform_subtitle(
            {
                "en": [{"ext": "vtt", "url": "https://captions.example/en"}],
                "zh-Hans": [
                    {"ext": "json3", "url": "https://captions.example/zh-json"},
                    {"ext": "vtt", "url": "https://captions.example/zh-vtt"},
                ],
            }
        )
        self.assertIsNotNone(selected)
        language, track = selected or ("", {})
        self.assertEqual(language, "zh-Hans")
        self.assertEqual(track["ext"], "vtt")

    def test_platform_url_keeps_only_public_youtube_identity(self) -> None:
        descriptor = classify_video_url(
            "https://www.youtube.com/watch?v=public-id&si=tracking-secret#fragment"
        )
        self.assertEqual(descriptor.source_kind, "platform_url")
        self.assertEqual(descriptor.platform, "youtube")
        self.assertEqual(
            descriptor.display_url,
            "https://www.youtube.com/watch?v=public-id",
        )

    def test_generic_signed_url_is_redacted_in_receipt(self) -> None:
        response = _FakeResponse(b"small-video-payload")
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch(
                "audience_mirror.media.source._open_public_url",
                return_value=(
                    response,
                    "https://cdn.example.com/video.mp4?token=remote-secret",
                    [],
                ),
            ):
                result = import_video_url(
                    "https://cdn.example.com/video.mp4?token=input-secret",
                    temporary_directory,
                )
            self.assertEqual(result.source_path.read_bytes(), b"small-video-payload")
            self.assertEqual(result.metadata["display_url"], "https://cdn.example.com/")
            self.assertEqual(result.metadata["resolved_url"], "https://cdn.example.com/")
            self.assertNotIn("secret", str(result.metadata))
            self.assertFalse(result.metadata["sensitive_query_parameters_persisted"])
            self.assertTrue(response.closed)

    def test_generic_path_bearer_is_not_persisted_or_used_as_filename(self) -> None:
        response = _FakeResponse(b"small-video-payload")
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch(
                "audience_mirror.media.source._open_public_url",
                return_value=(
                    response,
                    "https://cdn.example.com/private/path-secret/video.mp4",
                    [],
                ),
            ):
                result = import_video_url(
                    "https://cdn.example.com/private/input-secret/video.mp4",
                    temporary_directory,
                )
            self.assertEqual(result.source_path.name, "linked-video.mp4")
            self.assertEqual(result.metadata["display_url"], "https://cdn.example.com/")
            self.assertEqual(result.metadata["resolved_url"], "https://cdn.example.com/")
            self.assertNotIn("secret", str(result.metadata))

    def test_credentials_are_rejected(self) -> None:
        with self.assertRaisesRegex(SourceImportError, "用户名或密码"):
            classify_video_url("https://user:password@example.com/video.mp4")

    def test_private_network_destination_is_rejected(self) -> None:
        answer = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))]
        with patch("audience_mirror.media.source.socket.getaddrinfo", return_value=answer):
            with self.assertRaisesRegex(SourceImportError, "内网"):
                _assert_public_destination("https://example.com/video.mp4")

    def test_size_limit_removes_partial_file(self) -> None:
        response = _FakeResponse(b"payload-larger-than-limit")
        with tempfile.TemporaryDirectory() as temporary_directory:
            with patch(
                "audience_mirror.media.source._open_public_url",
                return_value=(response, "https://cdn.example.com/video.mp4", []),
            ):
                with self.assertRaisesRegex(SourceImportError, "超过"):
                    import_video_url(
                        "https://cdn.example.com/video.mp4",
                        temporary_directory,
                        max_bytes=4,
                    )
            self.assertEqual(list(Path(temporary_directory).iterdir()), [])

    def test_platform_selector_prefers_bounded_mp4_pair_without_drc(self) -> None:
        formats = [
            {"format_id": "video-hls", "ext": "mp4", "height": 720, "vcodec": "avc1", "acodec": "none", "protocol": "m3u8", "tbr": 4000},
            {"format_id": "video-http", "ext": "mp4", "height": 720, "vcodec": "avc1", "acodec": "none", "protocol": "https", "tbr": 1800, "filesize": 120_000_000},
            {"format_id": "audio-drc", "ext": "m4a", "vcodec": "none", "acodec": "mp4a", "abr": 128, "filesize": 8_000_000},
            {"format_id": "audio-clean", "ext": "m4a", "vcodec": "none", "acodec": "mp4a", "abr": 128, "filesize": 8_000_000},
        ]
        video, audio = _choose_platform_formats(formats, max_bytes=150_000_000)
        self.assertEqual(video["format_id"], "video-http")
        self.assertEqual(audio["format_id"], "audio-clean")

    def test_platform_streams_share_one_download_budget(self) -> None:
        budget = _DownloadBudget(max_bytes=10, deadline=float("inf"), downloaded_by_stream={})
        budget.check("video", 6)
        with self.assertRaisesRegex(SourceImportError, "合计超过"):
            budget.check("audio", 5)

    def test_platform_budget_enforces_wall_clock_deadline(self) -> None:
        budget = _DownloadBudget(max_bytes=10, deadline=0, downloaded_by_stream={})
        with self.assertRaisesRegex(SourceImportError, "30 分钟"):
            budget.check("video", 1)

    def test_platform_live_and_unknown_duration_fail_closed(self) -> None:
        with self.assertRaisesRegex(SourceImportError, "不支持直播"):
            _validated_platform_duration_seconds(
                {"is_live": True, "live_status": "is_live", "duration": None}
            )
        with self.assertRaisesRegex(SourceImportError, "未提供可确认的时长"):
            _validated_platform_duration_seconds({"is_live": False})

    def test_platform_declared_duration_must_fit_four_hour_limit(self) -> None:
        self.assertEqual(_validated_platform_duration_seconds({"duration": 60}), 60.0)
        with self.assertRaisesRegex(SourceImportError, "超过 4 小时"):
            _validated_platform_duration_seconds({"duration": 4 * 60 * 60 + 1})
