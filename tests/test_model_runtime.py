from __future__ import annotations

import json
import unittest
from pathlib import Path

from audience_mirror.domain import RunConfig
from audience_mirror.model_runtime import ModelSequentialRuntime
from audience_mirror.reasoning import ReasoningResult
from audience_mirror.universe import SyntheticPersonaUniverse
from audience_mirror.validation import validate_trace_stream


ROOT = Path(__file__).resolve().parents[1]


class StaticReasoner:
    provider = "test-structured-reasoner"
    model_id = "test-model"

    def __init__(self) -> None:
        self.calls = 0

    def respond_json(self, prompt, schema):
        self.calls += 1
        return ReasoningResult(
            value={
                "state_after": {
                    "attention_proxy": 0.72,
                    "valence": 0.15,
                    "arousal": 0.55,
                    "comprehension": 0.68,
                    "confusion": 0.22,
                    "trust": 0.61,
                    "continue_intent": 0.75,
                    "share_intent": 0.35,
                    "consider_paying": 0.3,
                    "uncertainty": 0.29,
                },
                "reaction_type": "understanding",
                "reaction_summary": "理解了当前事件。",
                "decision_basis_summary": "仅依据当前可见事件和此前记忆。",
                "confidence": 0.71,
                "action_type": "continue",
                "action_reason": "继续体验。",
                "memory_summary": "记住当前事件。",
                "perceived_facts": ["当前事件已发生。"],
                "open_questions": ["下一步会发生什么？"],
            },
            provider=self.provider,
            model_id=self.model_id,
            model_version="test-v1",
            latency_ms=3,
            input_tokens=100,
            output_tokens=50,
        )


class ModelSequentialRuntimeTests(unittest.TestCase):
    def test_structured_model_is_called_once_per_visible_event(self) -> None:
        timeline = json.loads(
            (ROOT / "fixtures" / "public-demo" / "timeline.json").read_text(encoding="utf-8")
        )
        config = RunConfig(pool_size=100, deep_count=1, sweep_count=1, projection_count=100)
        persona = SyntheticPersonaUniverse(100, config.seed).cohort(1)
        reasoner = StaticReasoner()
        traces = ModelSequentialRuntime(reasoner).run_deep(timeline, persona, config)
        self.assertEqual(reasoner.calls, 4)
        self.assertEqual(len(traces), 4)
        self.assertTrue(all(trace["extensions"]["model_driven"] for trace in traces))
        self.assertTrue(all(trace["provenance"]["provenance_type"] == "model" for trace in traces))
        self.assertEqual(traces[-1]["event_type"], "session.completed")
        validate_trace_stream(traces, timeline)
