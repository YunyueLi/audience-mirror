from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from audience_mirror.static_demo import (
    STATIC_DEMO_SCHEMA_VERSION,
    build_static_demo_bundle,
    export_static_demo,
)


class StaticDemoTests(unittest.TestCase):
    def test_bundle_is_synthetic_read_only_and_has_no_humans(self) -> None:
        bundle = build_static_demo_bundle()
        self.assertEqual(bundle["schema_version"], STATIC_DEMO_SCHEMA_VERSION)
        self.assertEqual(bundle["health"]["deployment_mode"], "static_public_demo")
        capabilities = bundle["health"]["capabilities"]
        self.assertTrue(capabilities["static_public_demo"])
        self.assertTrue(capabilities["environment_contract"])
        for capability in (
            "local_video_decode",
            "direct_video_url",
            "platform_video_url",
            "gemini_native_video",
            "codex_frame_analysis",
            "human_calibration",
        ):
            self.assertFalse(capabilities[capability])
        experiment = bundle["experiment"]
        self.assertEqual(experiment["experiment_id"], "demo")
        self.assertEqual(experiment["counts"]["persona_pool_records"], 10_000)
        self.assertEqual(experiment["counts"]["deep_personas"], 6)
        self.assertEqual(experiment["counts"]["human_participants"], 0)
        self.assertIsNone(experiment["media_url"])
        self.assertEqual(experiment["frame_urls"], {})

    def test_export_is_browser_javascript_with_same_payload(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = export_static_demo(Path(directory) / "static-demo.js")
            text = path.read_text(encoding="utf-8")
            prefix = "window.__AUDIENCE_MIRROR_STATIC_DEMO__="
            payload_text = text.split(prefix, 1)[1].rstrip(";\n")
            payload = json.loads(payload_text)
            self.assertEqual(payload["schema_version"], STATIC_DEMO_SCHEMA_VERSION)
            self.assertEqual(payload["health"]["privacy"]["human_records"], 0)


if __name__ == "__main__":
    unittest.main()
