from __future__ import annotations

import importlib.util
import unittest


@unittest.skipUnless(importlib.util.find_spec("fastapi"), "web extra is not installed")
class WorkbenchApiTests(unittest.TestCase):
    def test_health_and_demo_are_available(self) -> None:
        from audience_mirror.webapp import create_app

        app = create_app()
        routes = {route.path: route for route in app.routes if hasattr(route, "endpoint")}
        health = routes["/api/health"].endpoint()
        self.assertTrue(health["capabilities"]["environment_contract"])

        payload = routes["/api/experiments/{experiment_id}"].endpoint("demo")
        self.assertEqual(payload["counts"]["persona_pool_records"], 10_000)
        self.assertEqual(payload["counts"]["deep_personas"], 6)
        self.assertEqual(payload["counts"]["human_participants"], 0)
        self.assertEqual(payload["environment"]["environment_type"], "media")
        self.assertIn("/api/experiments/{experiment_id}/media/video", routes)
        self.assertIn("/api/experiments/{experiment_id}/media/audio", routes)
