from __future__ import annotations

import json
import unittest
from pathlib import Path

from audience_mirror.calibration import calibrate_traces
from audience_mirror.domain import RunConfig
from audience_mirror.runtime import DeterministicMediaRuntime
from audience_mirror.universe import SyntheticPersonaUniverse
from audience_mirror.validation import timeline_hash


ROOT = Path(__file__).resolve().parents[1]


class CalibrationTests(unittest.TestCase):
    def test_repository_fixture_demonstrates_withdrawal_and_ab_reporting(self) -> None:
        timeline = json.loads(
            (ROOT / "fixtures" / "public-demo" / "timeline.json").read_text(encoding="utf-8")
        )
        payload = json.loads(
            (ROOT / "fixtures" / "public-demo" / "human-anchors.synthetic.json").read_text(encoding="utf-8")
        )
        config = RunConfig(
            experiment_id="exp-workbench-demo",
            pool_size=100,
            deep_count=2,
            sweep_count=1,
            projection_count=100,
        )
        personas = SyntheticPersonaUniverse(100, config.seed).cohort(2)
        traces = DeterministicMediaRuntime().run_deep(timeline, personas, config)
        report = calibrate_traces(traces, payload["anchors"], agent_ab_direction="variant_a")
        self.assertEqual(report["scope"]["human_participants"], 3)
        self.assertEqual(report["scope"]["withdrawn_anchors_excluded"], 1)
        self.assertTrue(report["ab_direction"]["direction_agreement"])

    def test_mismatched_timeline_is_rejected(self) -> None:
        timeline = json.loads(
            (ROOT / "fixtures" / "public-demo" / "timeline.json").read_text(encoding="utf-8")
        )
        payload = json.loads(
            (ROOT / "fixtures" / "public-demo" / "human-anchors.synthetic.json").read_text(encoding="utf-8")
        )
        config = RunConfig(
            experiment_id="another-experiment",
            pool_size=100,
            deep_count=2,
            sweep_count=1,
            projection_count=100,
        )
        personas = SyntheticPersonaUniverse(100, config.seed).cohort(2)
        traces = DeterministicMediaRuntime().run_deep(timeline, personas, config)
        with self.assertRaisesRegex(ValueError, "不一致"):
            calibrate_traces(traces, payload["anchors"])

    def test_active_human_anchors_remain_a_separate_sample_count(self) -> None:
        timeline = json.loads(
            (ROOT / "fixtures" / "public-demo" / "timeline.json").read_text(encoding="utf-8")
        )
        config = RunConfig(pool_size=100, deep_count=2, sweep_count=1, projection_count=100)
        personas = SyntheticPersonaUniverse(100, config.seed).cohort(2)
        traces = DeterministicMediaRuntime().run_deep(timeline, personas, config)
        traces[0]["extensions"]["issue_codes"] = ["confusion"]
        node = timeline["nodes"][1]
        anchor = {
            "schema_version": "audience-mirror.human-anchor/v0.1",
            "human_anchor_id": "anchor-1",
            "experiment_id": config.experiment_id,
            "human_session_id": "human-session-1",
            "assignment_id": "assignment-1",
            "exposure_order": 0,
            "counterbalance_cell": "not_applicable",
            "participant_pseudonym": "participant-1",
            "consent_ref": "consent:1",
            "consent_status": "active",
            "withdrawal": None,
            "segment_id": None,
            "asset": {key: timeline["asset"][key] for key in ("asset_id", "variant_id", "content_hash", "rights_manifest_id")},
            "comparison_asset": None,
            "data_handling": timeline["data_handling"],
            "instrument": {"instrument_id": "instrument-1", "instrument_type": "timestamp_issue", "version": "1", "scale_ref": None},
            "timeline": {
                "timeline_id": timeline["timeline_id"],
                "timeline_hash": timeline_hash(timeline),
                "timeline_node_id": node["node_id"],
                "t_start_ms": node["t_start_ms"],
                "t_end_ms": node["t_end_ms"],
            },
            "response": {
                "metric_id": "issue",
                "value": True,
                "direction": "not_applicable",
                "severity": "medium",
                "issue_code": "confusion",
                "summary": "公开合成测试锚点。",
                "confidence": 0.8,
            },
            "observed_at": "2026-08-20T00:00:00Z",
            "provenance": {
                "collection_system": "synthetic-test",
                "source_record_hash": "0" * 64,
                "source_record_ref": "source:1",
                "coder_ref": None,
                "coded_at": "2026-08-20T00:00:00Z",
            },
            "extensions": {},
        }
        report = calibrate_traces(traces, [anchor])
        self.assertEqual(report["scope"]["human_participants"], 1)
        self.assertEqual(report["scope"]["agent_sessions"], 2)
        self.assertFalse(report["scope"]["statistical_representativeness_claimed"])
        self.assertEqual(report["top_issue_recall"]["recall"], 1.0)
