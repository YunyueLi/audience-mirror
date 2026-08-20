"""Public video benchmark contracts and deterministic scoring.

The benchmark measures answer and evidence agreement on a fixed public asset.
It does not measure human preference prediction and never upgrades Persona or
model runs into a human sample size.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from itertools import combinations
from statistics import mean, pstdev
import re
import unicodedata
from typing import Any

from .hashing import fingerprint
from .reasoning import JsonReasoner
from .validation import validate_timeline


BENCHMARK_SCHEMA_VERSION = "audience-mirror.video-benchmark/v0.1"
PREDICTIONS_SCHEMA_VERSION = "audience-mirror.video-benchmark-predictions/v0.1"
REPORT_SCHEMA_VERSION = "audience-mirror.video-benchmark-report/v0.1"
STABILITY_REPORT_SCHEMA_VERSION = "audience-mirror.video-benchmark-stability/v0.1"

BENCHMARK_PREDICTIONS_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["predictions"],
    "properties": {
        "predictions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "question_id",
                    "answer_text",
                    "answer_order",
                    "answer_t_start_ms",
                    "answer_t_end_ms",
                    "evidence",
                ],
                "properties": {
                    "question_id": {"type": "string"},
                    "answer_text": {"type": "string"},
                    "answer_order": {"type": "array", "items": {"type": "string"}},
                    "answer_t_start_ms": {"type": "integer", "minimum": -1},
                    "answer_t_end_ms": {"type": "integer", "minimum": -1},
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["t_start_ms", "t_end_ms"],
                            "properties": {
                                "t_start_ms": {"type": "integer", "minimum": 0},
                                "t_end_ms": {"type": "integer", "minimum": 1},
                            },
                        },
                    },
                },
            },
        }
    },
}

QUESTION_CATEGORIES = {
    "visual_fact",
    "ocr_text",
    "dialogue",
    "temporal_localization",
    "temporal_order",
    "cross_event",
}
ANSWER_TYPES = {"short_text", "multiple_choice", "time_range", "ordered_choices", "boolean"}
SCORING_STRATEGIES = {
    "exact",
    "contains",
    "choice",
    "time_overlap",
    "ordered_exact",
    "required_terms",
}


def _normalise_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"[^\w\u3400-\u9fff]+", "", text)


def _time_range(value: Any, context: str) -> tuple[int, int]:
    if not isinstance(value, dict):
        raise ValueError(f"{context}: expected an object with t_start_ms and t_end_ms")
    start = value.get("t_start_ms")
    end = value.get("t_end_ms")
    if isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int) or not isinstance(end, int):
        raise ValueError(f"{context}: t_start_ms and t_end_ms must be integers")
    if start < 0 or end <= start:
        raise ValueError(f"{context}: expected 0 <= t_start_ms < t_end_ms")
    return start, end


def _interval_iou(left: tuple[int, int], right: tuple[int, int]) -> float:
    intersection = max(0, min(left[1], right[1]) - max(left[0], right[0]))
    union = max(left[1], right[1]) - min(left[0], right[0])
    return intersection / union if union else 0.0


def validate_video_benchmark(benchmark: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "benchmark_id",
        "title",
        "asset",
        "construction",
        "questions",
        "limitations",
    }
    if not isinstance(benchmark, dict):
        raise ValueError("benchmark: expected an object")
    errors: list[str] = []
    missing = required - set(benchmark)
    if missing:
        errors.append(f"benchmark: missing {', '.join(sorted(missing))}")
    if benchmark.get("schema_version") != BENCHMARK_SCHEMA_VERSION:
        errors.append("benchmark.schema_version: unsupported value")
    benchmark_id = benchmark.get("benchmark_id")
    if not isinstance(benchmark_id, str) or not benchmark_id:
        errors.append("benchmark.benchmark_id: expected non-empty string")
    asset = benchmark.get("asset", {})
    duration_ms = asset.get("duration_ms")
    if isinstance(duration_ms, bool) or not isinstance(duration_ms, int) or duration_ms <= 0:
        errors.append("benchmark.asset.duration_ms: expected positive integer")
        duration_ms = 0
    questions = benchmark.get("questions")
    if not isinstance(questions, list) or not questions:
        errors.append("benchmark.questions: expected non-empty array")
        questions = []
    seen: set[str] = set()
    for index, question in enumerate(questions):
        context = f"benchmark.questions[{index}]"
        if not isinstance(question, dict):
            errors.append(f"{context}: expected object")
            continue
        question_id = question.get("question_id")
        if not isinstance(question_id, str) or not question_id:
            errors.append(f"{context}.question_id: expected non-empty string")
        elif question_id in seen:
            errors.append(f"{context}.question_id: duplicate")
        else:
            seen.add(question_id)
        category = question.get("category")
        if category not in QUESTION_CATEGORIES:
            errors.append(f"{context}.category: unsupported value")
        answer_type = question.get("answer_type")
        if answer_type not in ANSWER_TYPES:
            errors.append(f"{context}.answer_type: unsupported value")
        scoring = question.get("scoring", {})
        if scoring.get("strategy") not in SCORING_STRATEGIES:
            errors.append(f"{context}.scoring.strategy: unsupported value")
        reference = question.get("reference", {})
        try:
            if answer_type == "time_range":
                reference_range = _time_range(reference.get("time_range_ms"), f"{context}.reference.time_range_ms")
                if duration_ms and reference_range[1] > duration_ms:
                    errors.append(f"{context}.reference.time_range_ms: exceeds asset duration")
            elif scoring.get("strategy") == "required_terms":
                groups = reference.get("required_term_groups")
                if (
                    not isinstance(groups, list)
                    or not groups
                    or any(not isinstance(group, list) or not group for group in groups)
                ):
                    errors.append(f"{context}.reference.required_term_groups: expected non-empty groups")
            elif not isinstance(reference.get("accepted_answers"), list) or not reference.get("accepted_answers"):
                errors.append(f"{context}.reference.accepted_answers: expected non-empty array")
        except ValueError as exc:
            errors.append(str(exc))
        evidence = question.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{context}.evidence: expected non-empty array")
            continue
        for evidence_index, item in enumerate(evidence):
            try:
                evidence_range = _time_range(item, f"{context}.evidence[{evidence_index}]")
                if duration_ms and evidence_range[1] > duration_ms:
                    errors.append(f"{context}.evidence[{evidence_index}]: exceeds asset duration")
            except ValueError as exc:
                errors.append(str(exc))
    if errors:
        raise ValueError("\n".join(errors))


def validate_benchmark_predictions(predictions: dict[str, Any], benchmark: dict[str, Any]) -> None:
    validate_video_benchmark(benchmark)
    errors: list[str] = []
    if not isinstance(predictions, dict):
        raise ValueError("predictions: expected an object")
    if predictions.get("schema_version") != PREDICTIONS_SCHEMA_VERSION:
        errors.append("predictions.schema_version: unsupported value")
    if predictions.get("benchmark_id") != benchmark["benchmark_id"]:
        errors.append("predictions.benchmark_id: does not match benchmark")
    values = predictions.get("predictions")
    if not isinstance(values, list):
        errors.append("predictions.predictions: expected array")
        values = []
    allowed = {item["question_id"] for item in benchmark["questions"]}
    seen: set[str] = set()
    for index, prediction in enumerate(values):
        context = f"predictions.predictions[{index}]"
        if not isinstance(prediction, dict):
            errors.append(f"{context}: expected object")
            continue
        question_id = prediction.get("question_id")
        if question_id not in allowed:
            errors.append(f"{context}.question_id: unknown question")
        elif question_id in seen:
            errors.append(f"{context}.question_id: duplicate")
        else:
            seen.add(question_id)
    if errors:
        raise ValueError("\n".join(errors))


def _score_answer(question: dict[str, Any], answer: Any) -> tuple[float, dict[str, Any]]:
    strategy = question["scoring"]["strategy"]
    reference = question["reference"]
    if strategy == "time_overlap":
        predicted = _time_range(answer, "prediction.answer")
        expected = _time_range(reference["time_range_ms"], "question.reference.time_range_ms")
        iou = _interval_iou(predicted, expected)
        threshold = float(question["scoring"].get("min_iou", 0.3))
        tolerance = int(question["scoring"].get("center_tolerance_ms", 0))
        predicted_center = (predicted[0] + predicted[1]) // 2
        expected_center = (expected[0] + expected[1]) // 2
        hit = iou >= threshold or abs(predicted_center - expected_center) <= tolerance
        return float(hit), {"interval_iou": round(iou, 6), "hit": hit}
    if strategy == "required_terms":
        predicted_text = _normalise_text(answer)
        groups = reference["required_term_groups"]
        hit = all(
            any(_normalise_text(term) in predicted_text for term in group)
            for group in groups
        )
        return float(hit), {"hit": hit, "required_groups": len(groups)}
    accepted = reference["accepted_answers"]
    if strategy == "ordered_exact":
        predicted_order = answer if isinstance(answer, list) else str(answer or "").split(",")
        expected_orders = [value if isinstance(value, list) else [value] for value in accepted]
        normalised = [_normalise_text(value) for value in predicted_order]
        hit = any(normalised == [_normalise_text(value) for value in order] for order in expected_orders)
        return float(hit), {"hit": hit}
    predicted_text = _normalise_text(answer)
    accepted_text = [_normalise_text(value) for value in accepted]
    if strategy == "contains":
        hit = any(value and value in predicted_text for value in accepted_text)
    else:
        hit = predicted_text in accepted_text
    return float(hit), {"hit": hit}


def _score_evidence(question: dict[str, Any], prediction: dict[str, Any]) -> tuple[float | None, float | None]:
    predicted_evidence = prediction.get("evidence")
    if not isinstance(predicted_evidence, list) or not predicted_evidence:
        return None, None
    expected_ranges = [
        _time_range(item, "question.evidence")
        for item in question["evidence"]
    ]
    best = 0.0
    for item in predicted_evidence:
        try:
            predicted_range = _time_range(item, "prediction.evidence")
        except ValueError:
            continue
        best = max(best, *(_interval_iou(predicted_range, expected) for expected in expected_ranges))
    threshold = float(question["scoring"].get("evidence_min_iou", 0.1))
    return round(best, 6), float(best >= threshold)


def _is_abstention(answer: Any) -> bool:
    if isinstance(answer, dict):
        start = answer.get("t_start_ms")
        end = answer.get("t_end_ms")
        return not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start
    if isinstance(answer, list):
        return not answer
    value = _normalise_text(answer)
    return value in {"", "unknown", "未知", "无法判断", "证据不足", "notavailable", "na"}


def score_benchmark_predictions(
    benchmark: dict[str, Any], predictions: dict[str, Any]
) -> dict[str, Any]:
    validate_benchmark_predictions(predictions, benchmark)
    by_id = {item["question_id"]: item for item in predictions["predictions"]}
    details: list[dict[str, Any]] = []
    category_scores: dict[str, list[float]] = defaultdict(list)
    evidence_ious: list[float] = []
    evidence_hits: list[float] = []
    temporal_ious: list[float] = []
    answered = 0
    abstained = 0
    submitted = 0
    for question in benchmark["questions"]:
        prediction = by_id.get(question["question_id"])
        if prediction is None or "answer" not in prediction:
            score = 0.0
            answer_detail: dict[str, Any] = {"hit": False, "reason": "unanswered"}
            evidence_iou = evidence_hit = None
        elif _is_abstention(prediction["answer"]):
            submitted += 1
            abstained += 1
            score = 0.0
            answer_detail = {"hit": False, "reason": "abstained"}
            evidence_iou = evidence_hit = None
        else:
            submitted += 1
            answered += 1
            try:
                score, answer_detail = _score_answer(question, prediction["answer"])
            except ValueError as exc:
                score, answer_detail = 0.0, {"hit": False, "reason": str(exc)}
            evidence_iou, evidence_hit = _score_evidence(question, prediction)
        if "interval_iou" in answer_detail:
            temporal_ious.append(float(answer_detail["interval_iou"]))
        if evidence_iou is not None:
            evidence_ious.append(evidence_iou)
            evidence_hits.append(float(evidence_hit))
        category_scores[question["category"]].append(score)
        details.append(
            {
                "question_id": question["question_id"],
                "category": question["category"],
                "score": round(score, 6),
                "answer_detail": answer_detail,
                "evidence_iou": evidence_iou,
                "evidence_hit": bool(evidence_hit) if evidence_hit is not None else None,
            }
        )
    scores = [item["score"] for item in details]
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "benchmark_id": benchmark["benchmark_id"],
        "run": deepcopy(predictions.get("run", {})),
        "scope": {
            "questions": len(benchmark["questions"]),
            "submitted": submitted,
            "answered": answered,
            "abstained": abstained,
            "unanswered": len(benchmark["questions"]) - submitted,
            "annotation_status": benchmark["construction"].get("annotation_status"),
            "human_annotator_count": benchmark["construction"].get("human_annotator_count"),
        },
        "answer_accuracy": {
            "macro_score": round(mean(scores), 6) if scores else None,
            "by_category": {
                category: {
                    "questions": len(values),
                    "macro_score": round(mean(values), 6),
                }
                for category, values in sorted(category_scores.items())
            },
        },
        "temporal_localization": {
            "scored_questions": len(temporal_ious),
            "mean_interval_iou": round(mean(temporal_ious), 6) if temporal_ious else None,
        },
        "evidence_grounding": {
            "predictions_with_evidence": len(evidence_ious),
            "mean_best_iou": round(mean(evidence_ious), 6) if evidence_ious else None,
            "hit_rate": round(mean(evidence_hits), 6) if evidence_hits else None,
        },
        "details": details,
        "limitations": [
            *benchmark.get("limitations", []),
            "该报告衡量固定公开题集上的答案与时间证据一致性，不衡量真人偏好预测。",
            "公开题集可能被模型训练数据或视频标题污染，应另做去标题与隐藏题对照。",
        ],
    }


STABILITY_CONDITION_KEYS = (
    "provider",
    "model_id",
    "model_version",
    "strategy",
    "timeline_hash",
    "original_video_seen",
    "audio_seen",
)


def _canonical_answer(question: dict[str, Any], prediction: dict[str, Any] | None) -> Any:
    if prediction is None or "answer" not in prediction or _is_abstention(prediction["answer"]):
        return None
    answer = prediction["answer"]
    if question["answer_type"] == "time_range":
        try:
            return _time_range(answer, "prediction.answer")
        except ValueError:
            return None
    if question["answer_type"] == "ordered_choices":
        values = answer if isinstance(answer, list) else str(answer or "").split(",")
        return tuple(_normalise_text(value) for value in values)
    return _normalise_text(answer)


def _pairwise_mean(values: list[Any], scorer: Any) -> tuple[int, float | None]:
    scores = [scorer(left, right) for left, right in combinations(values, 2)]
    return len(scores), round(mean(scores), 6) if scores else None


def _evidence_pair_iou(left: dict[str, Any], right: dict[str, Any]) -> float | None:
    left_values = left.get("evidence")
    right_values = right.get("evidence")
    if not isinstance(left_values, list) or not left_values or not isinstance(right_values, list) or not right_values:
        return None
    left_ranges: list[tuple[int, int]] = []
    right_ranges: list[tuple[int, int]] = []
    for item in left_values:
        try:
            left_ranges.append(_time_range(item, "prediction.evidence"))
        except ValueError:
            continue
    for item in right_values:
        try:
            right_ranges.append(_time_range(item, "prediction.evidence"))
        except ValueError:
            continue
    if not left_ranges or not right_ranges:
        return None
    return max(_interval_iou(a, b) for a in left_ranges for b in right_ranges)


def compare_benchmark_stability(
    benchmark: dict[str, Any], prediction_runs: list[dict[str, Any]]
) -> dict[str, Any]:
    """Measure repeat-run stability without treating repetitions as human samples.

    Runs must share the same provider, model, strategy and evidence condition.
    This deliberately refuses caption/no-caption or cross-model mixtures: those
    are experimental contrasts, not repeated measurements of one condition.
    """

    validate_video_benchmark(benchmark)
    if len(prediction_runs) < 2:
        raise ValueError("stability requires at least two prediction runs")
    for predictions in prediction_runs:
        validate_benchmark_predictions(predictions, benchmark)
    expected_conditions = {
        key: prediction_runs[0].get("run", {}).get(key)
        for key in STABILITY_CONDITION_KEYS
    }
    for index, predictions in enumerate(prediction_runs[1:], start=2):
        conditions = {
            key: predictions.get("run", {}).get(key)
            for key in STABILITY_CONDITION_KEYS
        }
        if conditions != expected_conditions:
            differing = [
                key for key in STABILITY_CONDITION_KEYS
                if conditions.get(key) != expected_conditions.get(key)
            ]
            raise ValueError(
                f"prediction run {index} is not a repeated condition; differs in {', '.join(differing)}"
            )

    run_reports = [score_benchmark_predictions(benchmark, run) for run in prediction_runs]
    by_run = [
        {item["question_id"]: item for item in run["predictions"]}
        for run in prediction_runs
    ]
    question_details: list[dict[str, Any]] = []
    status_scores: list[float] = []
    answer_scores: list[float] = []
    temporal_scores: list[float] = []
    evidence_scores: list[float] = []
    reference_scores_by_question = {
        question["question_id"]: [
            report["details"][index]["score"] for report in run_reports
        ]
        for index, question in enumerate(benchmark["questions"])
    }
    for question in benchmark["questions"]:
        question_id = question["question_id"]
        predictions = [values.get(question_id) for values in by_run]
        canonical = [_canonical_answer(question, item) for item in predictions]
        statuses = [value is not None for value in canonical]
        status_pairs, status_agreement = _pairwise_mean(
            statuses, lambda left, right: float(left == right)
        )
        if status_agreement is not None:
            status_scores.extend(
                float(left == right) for left, right in combinations(statuses, 2)
            )
        answered = [value for value in canonical if value is not None]
        if question["answer_type"] == "time_range":
            answer_pairs, answer_agreement = _pairwise_mean(answered, _interval_iou)
            if answer_agreement is not None:
                temporal_scores.extend(
                    _interval_iou(left, right) for left, right in combinations(answered, 2)
                )
        else:
            answer_pairs, answer_agreement = _pairwise_mean(
                answered, lambda left, right: float(left == right)
            )
            if answer_agreement is not None:
                answer_scores.extend(
                    float(left == right) for left, right in combinations(answered, 2)
                )
        evidence_values = [item for item in predictions if isinstance(item, dict)]
        pair_evidence = [
            score
            for left, right in combinations(evidence_values, 2)
            if (score := _evidence_pair_iou(left, right)) is not None
        ]
        evidence_scores.extend(pair_evidence)
        reference_scores = reference_scores_by_question[question_id]
        question_details.append(
            {
                "question_id": question_id,
                "category": question["category"],
                "answered_runs": sum(statuses),
                "status_pairs": status_pairs,
                "status_agreement": status_agreement,
                "answer_pairs": answer_pairs,
                "answer_agreement": answer_agreement,
                "evidence_pairs": len(pair_evidence),
                "mean_evidence_iou": round(mean(pair_evidence), 6) if pair_evidence else None,
                "reference_score_mean": round(mean(reference_scores), 6),
                "reference_score_range": round(max(reference_scores) - min(reference_scores), 6),
            }
        )

    macro_scores = [report["answer_accuracy"]["macro_score"] for report in run_reports]
    abstentions = [report["scope"]["abstained"] for report in run_reports]
    unstable = [
        item["question_id"]
        for item in question_details
        if item["status_agreement"] != 1.0
        or (item["answer_agreement"] is not None and item["answer_agreement"] < 1.0)
        or item["reference_score_range"] > 0
    ]
    status_unstable = [
        item["question_id"] for item in question_details
        if item["status_agreement"] != 1.0
    ]
    verbatim_unstable = [
        item["question_id"] for item in question_details
        if item["answer_agreement"] is not None and item["answer_agreement"] < 1.0
    ]
    score_unstable = [
        item["question_id"] for item in question_details
        if item["reference_score_range"] > 0
    ]
    evidence_unstable = [
        item["question_id"] for item in question_details
        if item["mean_evidence_iou"] is not None and item["mean_evidence_iou"] < 1.0
    ]
    return {
        "schema_version": STABILITY_REPORT_SCHEMA_VERSION,
        "benchmark_id": benchmark["benchmark_id"],
        "conditions": expected_conditions,
        "scope": {
            "runs": len(prediction_runs),
            "questions": len(benchmark["questions"]),
            "agent_or_model_repetitions": len(prediction_runs),
            "human_sample_size": 0,
            "annotation_status": benchmark["construction"].get("annotation_status"),
        },
        "reference_score": {
            "macro_mean": round(mean(macro_scores), 6),
            "macro_min": round(min(macro_scores), 6),
            "macro_max": round(max(macro_scores), 6),
            "macro_population_stddev": round(pstdev(macro_scores), 6),
        },
        "abstentions": {
            "mean": round(mean(abstentions), 6),
            "min": min(abstentions),
            "max": max(abstentions),
        },
        "repeatability": {
            "status_pairwise_agreement": round(mean(status_scores), 6) if status_scores else None,
            "answer_pairwise_exact_agreement": round(mean(answer_scores), 6) if answer_scores else None,
            "temporal_answer_mean_pairwise_iou": round(mean(temporal_scores), 6) if temporal_scores else None,
            "evidence_mean_pairwise_iou": round(mean(evidence_scores), 6) if evidence_scores else None,
            "unstable_questions": len(unstable),
            "unstable_question_ids": unstable,
            "status_unstable_questions": len(status_unstable),
            "status_unstable_question_ids": status_unstable,
            "verbatim_unstable_questions": len(verbatim_unstable),
            "verbatim_unstable_question_ids": verbatim_unstable,
            "reference_score_unstable_questions": len(score_unstable),
            "reference_score_unstable_question_ids": score_unstable,
            "evidence_unstable_questions": len(evidence_unstable),
            "evidence_unstable_question_ids": evidence_unstable,
        },
        "runs": [
            {
                "index": index + 1,
                "macro_score": report["answer_accuracy"]["macro_score"],
                "answered": report["scope"]["answered"],
                "abstained": report["scope"]["abstained"],
                "latency_ms": prediction_runs[index].get("run", {}).get("latency_ms"),
            }
            for index, report in enumerate(run_reports)
        ],
        "questions": question_details,
        "limitations": [
            "重复模型运行只衡量同一技术条件的稳定性，不增加真人样本量。",
            "答案文本完全一致率可能低估语义等价表达；参考得分与证据漂移需同时阅读。",
            "跨模型、字幕增量和策略差异是实验对照，不能混入同一稳定性报告。",
        ],
    }


def run_timeline_text_baseline(
    benchmark: dict[str, Any],
    timeline: dict[str, Any],
    reasoner: JsonReasoner,
) -> dict[str, Any]:
    """Answer the public benchmark from a compressed semantic Timeline.

    This is deliberately named a Timeline-text baseline. It does not let the
    reasoner inspect the original video, audio, frames or benchmark references.
    Missing modalities should therefore surface as unanswered or incorrect.
    """

    validate_video_benchmark(benchmark)
    validate_timeline(timeline)
    if timeline["asset"]["content_hash"] != benchmark["asset"]["content_hash"]:
        raise ValueError("benchmark asset hash does not match Timeline asset")
    event_nodes = sorted(
        (node for node in timeline["nodes"] if node.get("level") == "event"),
        key=lambda node: (node["t_start_ms"], node["node_id"]),
    )
    evidence_pack = [
        {
            "t_start_ms": node["t_start_ms"],
            "t_end_ms": node["t_end_ms"],
            "label": node["label"],
            "summary": node.get("summary"),
            "observations": [
                {
                    "modality": observation.get("modality"),
                    "kind": observation.get("kind"),
                    "text": observation.get("text"),
                }
                for observation in node.get("observations", [])
            ],
            "uncertainties": node.get("extensions", {}).get("model_uncertainties", []),
        }
        for node in event_nodes
    ]
    questions = [
        {
            "question_id": question["question_id"],
            "category": question["category"],
            "prompt": question["prompt"],
            "answer_type": question["answer_type"],
            "choices": question.get("choices"),
        }
        for question in benchmark["questions"]
    ]
    prompt = (
        "你正在运行 Audience Mirror 的 semantic_timeline_text 视频理解基线。\n"
        "你只能使用下面给出的按时间排序事件与观察，不能使用片名、外部知识或训练记忆补全。\n"
        "它不是原视频，也不保证含音频或字幕；证据不足时回答 unknown，不要猜测。\n"
        "必须为每道题输出一条 prediction，question_id 原样保留。\n"
        "每条输出固定包含 answer_text、answer_order、answer_t_start_ms、answer_t_end_ms。\n"
        "short_text／multiple_choice／boolean 只填写 answer_text；ordered_choices 只填写 answer_order；"
        "time_range 只填写两个时间字段。未使用的字符串为空、数组为空、时间为 -1。\n"
        "evidence 只引用下面事件中的时间范围，不得引用题目参考答案，因为参考答案并未提供。\n\n"
        f"TIMELINE_EVIDENCE={evidence_pack!r}\n\nQUESTIONS={questions!r}"
    )
    result = reasoner.respond_json(prompt, BENCHMARK_PREDICTIONS_RESPONSE_SCHEMA)
    answer_types = {question["question_id"]: question["answer_type"] for question in benchmark["questions"]}
    converted_predictions: list[dict[str, Any]] = []
    for item in result.value.get("predictions", []):
        if not isinstance(item, dict):
            continue
        question_id = item.get("question_id")
        answer_type = answer_types.get(question_id)
        if answer_type == "time_range":
            answer: Any = {
                "t_start_ms": item.get("answer_t_start_ms"),
                "t_end_ms": item.get("answer_t_end_ms"),
            }
        elif answer_type == "ordered_choices":
            answer = item.get("answer_order", [])
        else:
            answer = item.get("answer_text", "")
        converted_predictions.append(
            {
                "question_id": question_id,
                "answer": answer,
                "evidence": item.get("evidence", []),
            }
        )
    payload = {
        "schema_version": PREDICTIONS_SCHEMA_VERSION,
        "benchmark_id": benchmark["benchmark_id"],
        "run": {
            "provider": result.provider,
            "model_id": result.model_id,
            "model_version": result.model_version,
            "strategy": "semantic_timeline_text",
            "timeline_hash": fingerprint(timeline),
            "event_count": len(event_nodes),
            "model_calls": 1,
            "latency_ms": result.latency_ms,
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "estimated_cost_usd": result.estimated_cost_usd,
            "original_video_seen": False,
            "audio_seen": False,
        },
        "predictions": converted_predictions,
    }
    validate_benchmark_predictions(payload, benchmark)
    return payload
