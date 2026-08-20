from __future__ import annotations

import asyncio
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


@unittest.skipUnless(importlib.util.find_spec("fastapi"), "web extra is not installed")
class WorkbenchApiTests(unittest.TestCase):
    @staticmethod
    def _route(app, path: str, method: str):
        return next(
            route
            for route in app.routes
            if getattr(route, "path", None) == path and method in getattr(route, "methods", set())
        )

    def test_health_and_demo_are_available(self) -> None:
        from audience_mirror.webapp import create_app

        app = create_app()
        routes = {route.path: route for route in app.routes if hasattr(route, "endpoint")}
        health = routes["/api/health"].endpoint()
        self.assertTrue(health["capabilities"]["environment_contract"])
        self.assertTrue(health["capabilities"]["direct_video_url"])
        self.assertIn("codex_cli", health["capabilities"])
        self.assertIn("codex_frame_analysis", health["capabilities"])
        self.assertIn("youtube", health["privacy"]["supported_link_sources"])

        payload = routes["/api/experiments/{experiment_id}"].endpoint("demo")
        self.assertEqual(payload["counts"]["persona_pool_records"], 10_000)
        self.assertEqual(payload["counts"]["deep_personas"], 6)
        self.assertEqual(payload["counts"]["human_participants"], 0)
        self.assertEqual(payload["environment"]["environment_type"], "media")
        self.assertIn("/api/experiments/{experiment_id}/media/video", routes)
        self.assertIn("/api/experiments/{experiment_id}/media/audio", routes)

    def test_persisted_experiment_is_recovered_and_listed(self) -> None:
        from audience_mirror.io import read_json, write_json
        import audience_mirror.webapp as webapp

        timeline = read_json(webapp.REPOSITORY_ROOT / "fixtures" / "public-demo" / "timeline.json")
        experiment_id = "exp-a1b2c3d4e5f6"
        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_root = Path(temporary_directory) / "workbench"
            output_directory = artifact_root / experiment_id
            ingest_directory = output_directory / "ingest"
            source_directory = output_directory / "source"
            source_directory.mkdir(parents=True)
            (source_directory / "restored.mp4").write_bytes(b"restored-video")
            write_json(ingest_directory / "timeline.json", timeline)
            write_json(
                ingest_directory / "ingest-manifest.json",
                {
                    "schema_version": "audience-mirror.video-ingest/v0.1",
                    "generated_at": "2026-08-20T00:00:00Z",
                    "source_name": "restored.mp4",
                    "frames": [],
                    "audio": None,
                },
            )
            write_json(
                output_directory / "source-receipt.json",
                {
                    "source_kind": "upload",
                    "platform": "local_file",
                    "title": "恢复测试视频",
                    "retrieval_method": "multipart_upload",
                    "sensitive_query_parameters_persisted": False,
                    "public_content_identifier_persisted": False,
                },
            )
            with patch.object(webapp, "ARTIFACT_ROOT", artifact_root):
                app = webapp.create_app()
                listing = self._route(app, "/api/experiments", "GET").endpoint()
                payload = self._route(app, "/api/experiments/{experiment_id}", "GET").endpoint(experiment_id)

            self.assertEqual(listing["count"], 1)
            self.assertEqual(listing["experiments"][0]["experiment_id"], experiment_id)
            self.assertEqual(listing["experiments"][0]["title"], "恢复测试视频")
            self.assertEqual(payload["status"], "ingested")
            self.assertEqual(payload["source_name"], "restored.mp4")
            self.assertEqual(payload["media_url"], f"/api/experiments/{experiment_id}/media/video")

    def test_invalid_persisted_directory_is_skipped(self) -> None:
        import audience_mirror.webapp as webapp

        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_root = Path(temporary_directory) / "workbench"
            broken = artifact_root / "exp-ffffffffffff"
            broken.mkdir(parents=True)
            (broken / "unexpected.txt").write_text("broken", encoding="utf-8")
            with patch.object(webapp, "ARTIFACT_ROOT", artifact_root):
                app = webapp.create_app()
                listing = self._route(app, "/api/experiments", "GET").endpoint()
            self.assertEqual(listing["experiments"], [])

    def test_model_run_requires_per_run_remote_processing_confirmation(self) -> None:
        from audience_mirror.webapp import create_app

        app = create_app()
        routes = {route.path: route for route in app.routes if hasattr(route, "endpoint")}
        with self.assertRaises(Exception) as raised:
            routes["/api/experiments/{experiment_id}/run"].endpoint(
                "demo",
                runtime_mode="model",
                persona_count=1,
                reasoner="codex-cli",
                model="gpt-5.6-sol",
                effort="xhigh",
                max_budget_usd=0.1,
                agent_remote_processing_confirmed=False,
                agent_provider_policy_confirmed=False,
            )
        self.assertEqual(getattr(raised.exception, "status_code", None), 403)

    def test_link_source_flows_into_experiment_receipt(self) -> None:
        from audience_mirror.io import read_json
        from audience_mirror.media.ingest import VideoIngestResult
        from audience_mirror.media.source import VideoSourceImport
        import audience_mirror.webapp as webapp

        timeline = read_json(webapp.REPOSITORY_ROOT / "fixtures" / "public-demo" / "timeline.json")
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            source_path = temporary_root / "resolved.mp4"
            source_path.write_bytes(b"resolved-public-video")
            ingest_directory = temporary_root / "ingest"
            ingest_directory.mkdir()
            source_import = VideoSourceImport(
                source_path=source_path,
                metadata={
                    "source_kind": "direct_url",
                    "platform": "direct",
                    "display_url": "https://cdn.example.com/video.mp4",
                    "retrieval_method": "streamed_http",
                    "title": "video",
                    "sensitive_query_parameters_persisted": False,
                    "public_content_identifier_persisted": False,
                },
            )
            ingest_result = VideoIngestResult(
                timeline=timeline,
                manifest={"frames": [], "audio": None},
                output_directory=ingest_directory,
            )
            with (
                patch.object(webapp, "ARTIFACT_ROOT", temporary_root / "artifacts"),
                patch.object(webapp, "import_video_url", return_value=source_import),
                patch.object(webapp, "ingest_video", return_value=ingest_result),
            ):
                app = webapp.create_app()
                routes = {route.path: route for route in app.routes if hasattr(route, "endpoint")}
                payload = asyncio.run(
                    routes["/api/experiments"].endpoint(
                        file=None,
                        source_url="https://cdn.example.com/video.mp4?token=secret",
                        rights_confirmed=True,
                        classification="public",
                        export_policy="authorized",
                        sample_interval_ms=5_000,
                        scene_threshold=0.24,
                    )
                )
            self.assertEqual(payload["source"]["source_kind"], "direct_url")
            self.assertEqual(payload["source"]["display_url"], "https://cdn.example.com/video.mp4")
            self.assertNotIn("secret", str(payload))

    def test_failed_ingest_removes_staged_source_and_experiment_directory(self) -> None:
        from audience_mirror.media.source import VideoSourceImport
        import audience_mirror.webapp as webapp

        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact_root = Path(temporary_directory) / "artifacts"

            def fake_import(value, output_directory, *, max_bytes):
                source_path = Path(output_directory) / "linked-video.mp4"
                source_path.parent.mkdir(parents=True, exist_ok=True)
                source_path.write_bytes(b"not-a-decodable-video")
                return VideoSourceImport(
                    source_path=source_path,
                    metadata={
                        "source_kind": "direct_url",
                        "platform": "direct",
                        "display_url": "https://cdn.example.com/",
                    },
                )

            with (
                patch.object(webapp, "ARTIFACT_ROOT", artifact_root),
                patch.object(webapp, "import_video_url", side_effect=fake_import),
                patch.object(webapp, "ingest_video", side_effect=ValueError("decode failed")),
            ):
                app = webapp.create_app()
                routes = {route.path: route for route in app.routes if hasattr(route, "endpoint")}
                with self.assertRaises(Exception) as raised:
                    asyncio.run(
                        routes["/api/experiments"].endpoint(
                            file=None,
                            source_url="https://cdn.example.com/private/source.mp4",
                            rights_confirmed=True,
                            classification="public",
                            export_policy="authorized",
                            sample_interval_ms=5_000,
                            scene_threshold=0.24,
                        )
                    )
            self.assertEqual(getattr(raised.exception, "status_code", None), 422)
            self.assertFalse(artifact_root.exists() and any(artifact_root.iterdir()))
