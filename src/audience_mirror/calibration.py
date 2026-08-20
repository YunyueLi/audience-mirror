"""Human-anchor alignment and calibration diagnostics.

Calibration never upgrades Agent count into human sample size. The functions here
measure agreement on the same task and Timeline, and disclose when a metric cannot
be computed.
"""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any


REACTION_ISSUES = {
    "confusion": "confusion",
    "boredom": "dropoff",
    "frustration": "friction",
    "purchase_objection": "purchase_objection",
}


def validate_human_anchors(anchors: list[dict[str, Any]]) -> None:
    required = {
        "schema_version",
        "human_anchor_id",
        "experiment_id",
        "human_session_id",
        "participant_pseudonym",
        "consent_ref",
        "consent_status",
        "withdrawal",
        "asset",
        "data_handling",
        "instrument",
        "timeline",
        "response",
        "observed_at",
        "provenance",
    }
    errors: list[str] = []
    seen: set[str] = set()
    for index, anchor in enumerate(anchors):
        context = f"anchors[{index}]"
        if not isinstance(anchor, dict):
            errors.append(f"{context}: expected an object")
            continue
        missing = required - set(anchor)
        if missing:
            errors.append(f"{context}: missing {', '.join(sorted(missing))}")
        if anchor.get("schema_version") != "audience-mirror.human-anchor/v0.1":
            errors.append(f"{context}.schema_version: unsupported value")
        anchor_id = anchor.get("human_anchor_id")
        if not isinstance(anchor_id, str) or not anchor_id:
            errors.append(f"{context}.human_anchor_id: expected non-empty string")
        elif anchor_id in seen:
            errors.append(f"{context}.human_anchor_id: duplicate")
        else:
            seen.add(anchor_id)
        consent = anchor.get("consent_status")
        if consent not in {"active", "withdrawn"}:
            errors.append(f"{context}.consent_status: unsupported value")
        if consent == "withdrawn":
            if not isinstance(anchor.get("withdrawal"), dict):
                errors.append(f"{context}.withdrawal: required for withdrawn consent")
            handling = anchor.get("data_handling", {})
            if handling.get("export_policy") != "no_export" or handling.get("redaction_status") != "blocked":
                errors.append(f"{context}.data_handling: withdrawn records must be blocked and no_export")
    if errors:
        raise ValueError("\n".join(errors))


def _overlaps(trace: dict[str, Any], anchor: dict[str, Any]) -> bool:
    trace_timeline = trace.get("timeline", {})
    anchor_timeline = anchor.get("timeline", {})
    anchor_node = anchor_timeline.get("timeline_node_id")
    if anchor_node and anchor_node == trace_timeline.get("timeline_node_id"):
        return True
    return max(
        int(trace_timeline.get("t_start_ms", 0)), int(anchor_timeline.get("t_start_ms", 0))
    ) <= min(
        int(trace_timeline.get("t_end_ms", 0)), int(anchor_timeline.get("t_end_ms", 0))
    )


def _trace_issue_codes(trace: dict[str, Any]) -> set[str]:
    issues = set(str(value) for value in trace.get("extensions", {}).get("issue_codes", []) if value)
    reaction_type = trace.get("reaction", {}).get("reaction_type")
    if reaction_type in REACTION_ISSUES:
        issues.add(REACTION_ISSUES[reaction_type])
    if trace.get("action", {}).get("action_type") in {"skip", "abandon"}:
        issues.add("dropoff")
    return issues


def _majority_direction(anchors: list[dict[str, Any]]) -> tuple[str | None, dict[str, int]]:
    counts = Counter(
        anchor.get("response", {}).get("direction")
        for anchor in anchors
        if anchor.get("instrument", {}).get("instrument_type") == "ab_choice"
        and anchor.get("response", {}).get("direction") in {"variant_a", "variant_b", "no_difference"}
    )
    if not counts:
        return None, {}
    top = counts.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        return "tie", dict(counts)
    return top[0][0], dict(counts)


def calibrate_traces(
    traces: list[dict[str, Any]],
    anchors: list[dict[str, Any]],
    *,
    top_k: int = 10,
    agent_ab_direction: str | None = None,
) -> dict[str, Any]:
    validate_human_anchors(anchors)
    active = [anchor for anchor in anchors if anchor.get("consent_status") == "active"]
    trace_scopes = {
        (
            trace.get("experiment_id"),
            trace.get("timeline", {}).get("timeline_id"),
            trace.get("timeline", {}).get("timeline_hash"),
            trace.get("asset", {}).get("asset_id"),
            trace.get("asset", {}).get("variant_id"),
            trace.get("asset", {}).get("content_hash"),
        )
        for trace in traces
    }
    alignment_errors: list[str] = []
    for anchor in active:
        anchor_scope = (
            anchor.get("experiment_id"),
            anchor.get("timeline", {}).get("timeline_id"),
            anchor.get("timeline", {}).get("timeline_hash"),
            anchor.get("asset", {}).get("asset_id"),
            anchor.get("asset", {}).get("variant_id"),
            anchor.get("asset", {}).get("content_hash"),
        )
        if anchor_scope not in trace_scopes:
            alignment_errors.append(anchor.get("human_anchor_id", "unknown-anchor"))
    if alignment_errors:
        raise ValueError(
            "Human Anchors 与当前 Agent Trace 的实验、Timeline 或素材版本不一致："
            + ", ".join(alignment_errors)
        )
    withdrawn_count = len(anchors) - len(active)
    human_issue_counts = Counter(
        anchor.get("response", {}).get("issue_code")
        for anchor in active
        if anchor.get("response", {}).get("issue_code")
    )
    agent_issue_counts: Counter[str] = Counter()
    for trace in traces:
        agent_issue_counts.update(_trace_issue_codes(trace))

    human_top = [code for code, _ in human_issue_counts.most_common(top_k)]
    agent_top = [code for code, _ in agent_issue_counts.most_common(top_k)]
    issue_recall = (
        len(set(human_top) & set(agent_top)) / len(set(human_top))
        if human_top
        else None
    )

    timestamped_human_issues = [
        anchor for anchor in active if anchor.get("response", {}).get("issue_code")
    ]
    matched_timestamped = 0
    match_details: list[dict[str, Any]] = []
    for anchor in timestamped_human_issues:
        issue_code = anchor["response"]["issue_code"]
        candidate_traces = [trace for trace in traces if _overlaps(trace, anchor)]
        matched = any(issue_code in _trace_issue_codes(trace) for trace in candidate_traces)
        matched_timestamped += int(matched)
        match_details.append(
            {
                "human_anchor_id": anchor["human_anchor_id"],
                "issue_code": issue_code,
                "matched": matched,
                "candidate_trace_count": len(candidate_traces),
            }
        )
    timestamp_issue_recall = (
        matched_timestamped / len(timestamped_human_issues)
        if timestamped_human_issues
        else None
    )

    numeric_alignment: list[dict[str, Any]] = []
    for anchor in active:
        response = anchor.get("response", {})
        metric_id = response.get("metric_id")
        human_value = response.get("value")
        if metric_id not in {
            "attention_proxy",
            "valence",
            "arousal",
            "comprehension",
            "confusion",
            "trust",
            "continue_intent",
            "share_intent",
            "consider_paying",
            "uncertainty",
        } or isinstance(human_value, bool) or not isinstance(human_value, (int, float)):
            continue
        matching = [trace for trace in traces if _overlaps(trace, anchor)]
        values = [
            float(trace["state"]["after"][metric_id])
            for trace in matching
            if metric_id in trace.get("state", {}).get("after", {})
        ]
        if not values:
            continue
        agent_mean = mean(values)
        numeric_alignment.append(
            {
                "human_anchor_id": anchor["human_anchor_id"],
                "metric_id": metric_id,
                "human_value": float(human_value),
                "agent_mean_proxy": round(agent_mean, 6),
                "absolute_error": round(abs(agent_mean - float(human_value)), 6),
                "agent_trace_count": len(values),
            }
        )
    numeric_mae = mean(item["absolute_error"] for item in numeric_alignment) if numeric_alignment else None

    human_direction, direction_counts = _majority_direction(active)
    direction_agreement = (
        agent_ab_direction == human_direction
        if agent_ab_direction in {"variant_a", "variant_b", "no_difference"}
        and human_direction in {"variant_a", "variant_b", "no_difference"}
        else None
    )
    session_ids = {trace.get("session_id") for trace in traces if trace.get("session_id")}
    return {
        "schema_version": "audience-mirror.calibration-report/v0.1",
        "scope": {
            "agent_sessions": len(session_ids),
            "agent_trace_events": len(traces),
            "human_participants": len({anchor["participant_pseudonym"] for anchor in active}),
            "active_human_anchors": len(active),
            "withdrawn_anchors_excluded": withdrawn_count,
            "statistical_representativeness_claimed": False,
        },
        "top_issue_recall": {
            "top_k": top_k,
            "human_issue_codes": human_top,
            "agent_issue_codes": agent_top,
            "recall": round(issue_recall, 6) if issue_recall is not None else None,
        },
        "timestamp_issue_recall": {
            "matched": matched_timestamped,
            "total": len(timestamped_human_issues),
            "recall": round(timestamp_issue_recall, 6) if timestamp_issue_recall is not None else None,
            "details": match_details,
        },
        "numeric_proxy_alignment": {
            "comparable_anchor_count": len(numeric_alignment),
            "mean_absolute_error": round(numeric_mae, 6) if numeric_mae is not None else None,
            "details": numeric_alignment,
            "warning": "仅比较同名、同任务、同时间窗代理量；未经预注册量表映射不得解释为真实心理测量。",
        },
        "ab_direction": {
            "human_majority": human_direction,
            "human_counts": direction_counts,
            "agent_direction": agent_ab_direction,
            "direction_agreement": direction_agreement,
        },
        "limitations": [
            "Agent Session 数与真人参与者数分开报告；重复生成不增加真人样本量。",
            "本报告衡量同任务一致性，不证明票房、收入或现实比例预测能力。",
            "校准集与封存验收集应分开，避免对同一真人反馈过拟合。",
        ],
    }
