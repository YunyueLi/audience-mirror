from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from audience_mirror.domain import RunConfig
from audience_mirror.runtime import DeterministicMediaRuntime
from audience_mirror.universe import SyntheticPersonaUniverse
from audience_mirror.validation import (
    ContractValidationError,
    validate_timeline,
    validate_trace_stream,
)


ROOT = Path(__file__).resolve().parents[1]
TIMELINE_PATH = ROOT / "fixtures" / "public-demo" / "timeline.json"


def load_timeline() -> dict:
    return json.loads(TIMELINE_PATH.read_text(encoding="utf-8"))


class TimelineContractTests(unittest.TestCase):
    def test_public_fixture_is_valid(self) -> None:
        validate_timeline(load_timeline())

    def test_rejects_child_outside_parent(self) -> None:
        timeline = load_timeline()
        event = next(node for node in timeline["nodes"] if node["node_id"] == "event-1")
        event["t_end_ms"] = 130_000
        with self.assertRaises(ContractValidationError):
            validate_timeline(timeline)

    def test_rejects_duplicate_observation_id(self) -> None:
        timeline = load_timeline()
        timeline["nodes"][1]["observations"][0]["observation_id"] = timeline["nodes"][0]["observations"][0]["observation_id"]
        with self.assertRaises(ContractValidationError):
            validate_timeline(timeline)


class TraceContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.timeline = load_timeline()
        self.config = RunConfig(deep_count=3, sweep_count=3, pool_size=100, projection_count=100)
        self.universe = SyntheticPersonaUniverse(self.config.pool_size, self.config.seed)
        self.runtime = DeterministicMediaRuntime()

    def test_deep_runtime_emits_valid_hash_chained_traces(self) -> None:
        traces = self.runtime.run_deep(self.timeline, self.universe.cohort(3), self.config)
        self.assertEqual(len(traces), 12)
        validate_trace_stream(traces, self.timeline)
        first_session = [trace for trace in traces if trace["session_id"] == traces[0]["session_id"]]
        self.assertIsNone(first_session[0]["previous_event_hash"])
        self.assertEqual(first_session[1]["previous_event_hash"], first_session[0]["event_hash"])
        self.assertTrue(all(trace["cost"]["estimated_cost"] == 0 for trace in traces))

    def test_rejects_tampered_trace(self) -> None:
        traces = self.runtime.run_deep(self.timeline, self.universe.cohort(3), self.config)
        tampered = copy.deepcopy(traces)
        tampered[0]["state"]["after"]["confusion"] = 0.99
        with self.assertRaises(ContractValidationError):
            validate_trace_stream(tampered, self.timeline)

    def test_sweep_and_projection_do_not_claim_complete_viewing(self) -> None:
        sweep = self.runtime.run_sweep(self.timeline, self.universe.cohort(3), self.config)
        projection = self.runtime.project_population(self.timeline, self.universe, 100)
        self.assertTrue(all(item["completed_experience"] is False for item in sweep))
        self.assertTrue(all(item["model_calls"] == 0 for item in sweep))
        self.assertEqual(projection["llm_calls"], 0)
        self.assertEqual(projection["completed_experiences"], 0)
        self.assertFalse(projection["statistical_representativeness"])
