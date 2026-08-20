from __future__ import annotations

from copy import deepcopy
import json
import unittest
from pathlib import Path
import importlib.util

from audience_mirror.benchmark import (
    PREDICTIONS_SCHEMA_VERSION,
    compare_benchmark_stability,
    run_timeline_text_baseline,
    score_benchmark_predictions,
    validate_benchmark_predictions,
    validate_video_benchmark,
)
from audience_mirror.reasoning import ReasoningResult


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_PATH = ROOT / "fixtures" / "benchmarks" / "sintel-public-dev-v0.1.json"


def load_benchmark() -> dict:
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


def perfect_predictions(benchmark: dict) -> dict:
    values = []
    for question in benchmark["questions"]:
        if question["answer_type"] == "time_range":
            answer = question["reference"]["time_range_ms"]
        elif question["scoring"]["strategy"] == "required_terms":
            answer = " ".join(
                group[0] for group in question["reference"]["required_term_groups"]
            )
        else:
            answer = question["reference"]["accepted_answers"][0]
        evidence = [
            {
                "t_start_ms": question["evidence"][0]["t_start_ms"],
                "t_end_ms": question["evidence"][0]["t_end_ms"],
            }
        ]
        values.append(
            {
                "question_id": question["question_id"],
                "answer": answer,
                "evidence": evidence,
            }
        )
    return {
        "schema_version": PREDICTIONS_SCHEMA_VERSION,
        "benchmark_id": benchmark["benchmark_id"],
        "run": {
            "provider": "test",
            "model_id": "perfect-fixture",
            "strategy": "fixture",
        },
        "predictions": values,
    }


class PublicVideoBenchmarkTests(unittest.TestCase):
    def test_sintel_public_development_set_is_valid_and_explicitly_draft(self) -> None:
        benchmark = load_benchmark()
        validate_video_benchmark(benchmark)
        self.assertEqual(len(benchmark["questions"]), 31)
        self.assertEqual(benchmark["construction"]["human_annotator_count"], 1)
        self.assertFalse(benchmark["construction"]["independent_second_review"])
        self.assertEqual(benchmark["construction"]["annotation_status"], "single_maintainer_draft")
        self.assertFalse(benchmark["asset"]["media_included"])

    def test_perfect_predictions_score_answers_and_evidence_separately(self) -> None:
        benchmark = load_benchmark()
        report = score_benchmark_predictions(benchmark, perfect_predictions(benchmark))
        self.assertEqual(report["scope"]["answered"], 31)
        self.assertEqual(report["answer_accuracy"]["macro_score"], 1.0)
        self.assertEqual(report["evidence_grounding"]["hit_rate"], 1.0)
        self.assertEqual(report["temporal_localization"]["mean_interval_iou"], 1.0)

    def test_unanswered_questions_are_not_silently_dropped(self) -> None:
        benchmark = load_benchmark()
        payload = perfect_predictions(benchmark)
        payload["predictions"] = payload["predictions"][:2]
        report = score_benchmark_predictions(benchmark, payload)
        self.assertEqual(report["scope"]["answered"], 2)
        self.assertEqual(report["scope"]["submitted"], 2)
        self.assertEqual(report["scope"]["abstained"], 0)
        self.assertEqual(report["scope"]["unanswered"], 29)
        self.assertLess(report["answer_accuracy"]["macro_score"], 0.1)

    def test_unknown_and_invalid_time_ranges_are_counted_as_abstentions(self) -> None:
        benchmark = load_benchmark()
        payload = perfect_predictions(benchmark)
        payload["predictions"][0]["answer"] = "unknown"
        time_index = next(
            index
            for index, question in enumerate(benchmark["questions"])
            if question["answer_type"] == "time_range"
        )
        payload["predictions"][time_index]["answer"] = {"t_start_ms": -1, "t_end_ms": -1}
        report = score_benchmark_predictions(benchmark, payload)
        self.assertEqual(report["scope"]["submitted"], 31)
        self.assertEqual(report["scope"]["answered"], 29)
        self.assertEqual(report["scope"]["abstained"], 2)
        self.assertEqual(report["scope"]["unanswered"], 0)

    def test_mismatched_benchmark_and_out_of_range_evidence_are_rejected(self) -> None:
        benchmark = load_benchmark()
        payload = perfect_predictions(benchmark)
        payload["benchmark_id"] = "another-benchmark"
        with self.assertRaisesRegex(ValueError, "does not match"):
            validate_benchmark_predictions(payload, benchmark)

        invalid = deepcopy(benchmark)
        invalid["questions"][0]["evidence"][0]["t_end_ms"] = benchmark["asset"]["duration_ms"] + 1
        with self.assertRaisesRegex(ValueError, "exceeds asset duration"):
            validate_video_benchmark(invalid)

    def test_timeline_text_baseline_records_that_original_media_was_not_seen(self) -> None:
        timeline = json.loads(
            (ROOT / "fixtures" / "public-demo" / "timeline.json").read_text(encoding="utf-8")
        )
        benchmark = {
            "schema_version": "audience-mirror.video-benchmark/v0.1",
            "benchmark_id": "fixture-benchmark",
            "title": "Fixture",
            "asset": {
                "title": "Fixture",
                "source_url": "https://example.com/fixture",
                "duration_ms": timeline["duration_ms"],
                "content_hash": timeline["asset"]["content_hash"],
                "license": "synthetic fixture",
                "attribution": "Audience Mirror",
                "media_included": False,
            },
            "construction": {
                "created_at": "2026-08-20",
                "language": "zh-CN",
                "annotation_status": "single_maintainer_draft",
                "human_annotator_count": 1,
                "source_evidence": ["synthetic fixture"],
                "independent_second_review": False,
            },
            "questions": [
                {
                    "question_id": "fixture-01",
                    "category": "visual_fact",
                    "prompt": "第一个事件是什么？",
                    "answer_type": "short_text",
                    "reference": {"accepted_answers": ["维修员听到重复信号"]},
                    "evidence": [
                        {
                            "t_start_ms": 0,
                            "t_end_ms": 55_000,
                            "modalities": ["text"],
                            "source_type": "maintainer_viewing",
                            "note": "合成事件。",
                        }
                    ],
                    "scoring": {"strategy": "contains"},
                    "difficulty": "easy",
                    "tags": ["fixture"],
                }
            ],
            "limitations": ["synthetic fixture"],
        }

        class FakeReasoner:
            provider = "fake"
            model_id = "fake-model"

            def respond_json(self, prompt: str, schema: dict) -> ReasoningResult:
                self.prompt = prompt
                self.schema = schema
                return ReasoningResult(
                    value={
                        "predictions": [
                            {
                                "question_id": "fixture-01",
                                "answer_text": "维修员听到重复信号",
                                "answer_order": [],
                                "answer_t_start_ms": -1,
                                "answer_t_end_ms": -1,
                                "evidence": [{"t_start_ms": 0, "t_end_ms": 55_000}],
                            }
                        ]
                    },
                    provider=self.provider,
                    model_id=self.model_id,
                    model_version="test",
                    latency_ms=4,
                )

        reasoner = FakeReasoner()
        predictions = run_timeline_text_baseline(benchmark, timeline, reasoner)
        self.assertIn("不能使用片名", reasoner.prompt)
        self.assertFalse(predictions["run"]["original_video_seen"])
        self.assertFalse(predictions["run"]["audio_seen"])
        self.assertEqual(predictions["run"]["model_calls"], 1)
        self.assertEqual(
            score_benchmark_predictions(benchmark, predictions)["answer_accuracy"]["macro_score"],
            1.0,
        )

    def test_stability_report_separates_model_repetitions_from_humans(self) -> None:
        benchmark = load_benchmark()
        first = perfect_predictions(benchmark)
        first["run"].update(
            {
                "model_version": "test",
                "timeline_hash": "same",
                "original_video_seen": False,
                "audio_seen": False,
            }
        )
        second = deepcopy(first)
        report = compare_benchmark_stability(benchmark, [first, second])
        self.assertEqual(report["scope"]["runs"], 2)
        self.assertEqual(report["scope"]["human_sample_size"], 0)
        self.assertEqual(report["repeatability"]["status_pairwise_agreement"], 1.0)
        self.assertEqual(report["repeatability"]["answer_pairwise_exact_agreement"], 1.0)
        self.assertEqual(report["repeatability"]["evidence_mean_pairwise_iou"], 1.0)
        self.assertEqual(report["repeatability"]["unstable_questions"], 0)
        self.assertEqual(report["repeatability"]["reference_score_unstable_questions"], 0)
        if importlib.util.find_spec("jsonschema"):
            from jsonschema import Draft202012Validator

            schema = json.loads(
                (ROOT / "schemas" / "video-benchmark-stability.schema.json").read_text(encoding="utf-8")
            )
            Draft202012Validator(schema).validate(report)

    def test_stability_report_finds_answer_and_abstention_drift(self) -> None:
        benchmark = load_benchmark()
        first = perfect_predictions(benchmark)
        first["run"].update(
            {
                "model_version": "test",
                "timeline_hash": "same",
                "original_video_seen": False,
                "audio_seen": False,
            }
        )
        second = deepcopy(first)
        second["predictions"][0]["answer"] = "unknown"
        second["predictions"][1]["answer"] = "不同答案"
        report = compare_benchmark_stability(benchmark, [first, second])
        self.assertLess(report["repeatability"]["status_pairwise_agreement"], 1.0)
        self.assertLess(report["repeatability"]["answer_pairwise_exact_agreement"], 1.0)
        self.assertGreater(report["repeatability"]["status_unstable_questions"], 0)
        self.assertGreater(report["repeatability"]["reference_score_unstable_questions"], 0)
        self.assertIn(benchmark["questions"][0]["question_id"], report["repeatability"]["unstable_question_ids"])
        self.assertIn(benchmark["questions"][1]["question_id"], report["repeatability"]["unstable_question_ids"])

    def test_stability_rejects_mixed_model_or_timeline_conditions(self) -> None:
        benchmark = load_benchmark()
        first = perfect_predictions(benchmark)
        second = deepcopy(first)
        second["run"]["model_id"] = "another-model"
        with self.assertRaisesRegex(ValueError, "not a repeated condition"):
            compare_benchmark_stability(benchmark, [first, second])
