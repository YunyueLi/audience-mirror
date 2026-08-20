from __future__ import annotations

import json
import unittest
from pathlib import Path

from audience_mirror.environment import Action, TimelineMediaEnvironment, validate_environment_spec


ROOT = Path(__file__).resolve().parents[1]


class EnvironmentContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.timeline = json.loads(
            (ROOT / "fixtures" / "public-demo" / "timeline.json").read_text(encoding="utf-8")
        )

    def test_timeline_environment_is_future_blind_and_stateful(self) -> None:
        environment = TimelineMediaEnvironment(self.timeline)
        validate_environment_spec(environment.spec)
        self.assertEqual(environment.spec["observation_space"]["future_visibility"], "blocked")
        first = environment.reset("session-1")
        self.assertEqual(first.step_index, 0)
        second = environment.step("session-1", Action("continue"))
        self.assertEqual(second.observation.step_index, 1)
        rewound = environment.step("session-1", Action("rewind_requested"))
        self.assertEqual(rewound.observation.step_index, 0)
        abandoned = environment.step("session-1", Action("abandon"))
        self.assertTrue(abandoned.observation.terminal)

    def test_unknown_action_is_rejected(self) -> None:
        environment = TimelineMediaEnvironment(self.timeline)
        environment.reset("session-1")
        with self.assertRaises(ValueError):
            environment.step("session-1", Action("teleport"))
