from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest

from audience_mirror.blind_study import prepare_blind_study


ROOT = Path(__file__).resolve().parents[1]


class BlindStudyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.timeline_a = json.loads(
            (ROOT / "fixtures" / "public-demo" / "timeline.json").read_text(encoding="utf-8")
        )
        self.timeline_b = deepcopy(self.timeline_a)
        self.timeline_b["timeline_id"] = "timeline-public-fiction-v2"
        self.timeline_b["asset"]["variant_id"] = "variant-b"
        self.timeline_b["asset"]["content_hash"] = "b" * 64
        self.timeline_b["asset"]["object_ref"] = "fixture:asset:public-fiction:variant-b"

    def test_ab_packet_is_deterministic_balanced_and_identity_free(self) -> None:
        first = prepare_blind_study(self.timeline_a, self.timeline_b, participant_slots=11, seed=7)
        second = prepare_blind_study(self.timeline_a, self.timeline_b, participant_slots=11, seed=7)
        self.assertEqual(first["study_plan"]["study_id"], second["study_plan"]["study_id"])
        self.assertEqual(first["participant_pack"]["assignments"], second["participant_pack"]["assignments"])
        cells = [item["counterbalance_cell"] for item in first["participant_pack"]["assignments"]]
        self.assertLessEqual(abs(cells.count("ab") - cells.count("ba")), 1)
        self.assertEqual(first["participant_pack"]["participant_identity_fields"], [])
        self.assertTrue(first["study_plan"]["design"]["outcome_blinded"])
        self.assertFalse(first["study_plan"]["design"]["statistical_representativeness_claimed"])
        self.assertEqual(first["researcher_key"]["export_policy"], "no_export")

        if importlib.util.find_spec("jsonschema"):
            from jsonschema import Draft202012Validator

            schema = json.loads((ROOT / "schemas" / "blind-study.schema.json").read_text(encoding="utf-8"))
            Draft202012Validator(schema).validate(first["study_plan"])

    def test_single_variant_packet_does_not_claim_ab(self) -> None:
        packet = prepare_blind_study(self.timeline_a, participant_slots=8)
        self.assertEqual(packet["study_plan"]["design"]["variant_count"], 1)
        self.assertFalse(packet["study_plan"]["design"]["counterbalanced"])
        self.assertNotIn("ab_choice", [item["instrument_type"] for item in packet["study_plan"]["measures"]])
        self.assertNotIn("ab_direction_agreement", packet["study_plan"]["pre_registered_metrics"])

    def test_ab_packet_rejects_same_content_or_different_asset(self) -> None:
        same = deepcopy(self.timeline_a)
        same["timeline_id"] = "timeline-same-content"
        with self.assertRaisesRegex(ValueError, "different content hashes"):
            prepare_blind_study(self.timeline_a, same)
        other = deepcopy(self.timeline_b)
        other["asset"]["asset_id"] = "another-asset"
        with self.assertRaisesRegex(ValueError, "same conceptual asset_id"):
            prepare_blind_study(self.timeline_a, other)


if __name__ == "__main__":
    unittest.main()
