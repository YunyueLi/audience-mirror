"""Prepare reproducible, outcome-blinded exploratory human-study packets.

The packet contains participant slots, never identities. Consent records and
responses are collected separately as Human Anchors after authorization.
"""

from __future__ import annotations

from datetime import datetime, timezone
import random
from typing import Any

from .hashing import fingerprint
from .validation import timeline_hash, validate_timeline


BLIND_STUDY_SCHEMA_VERSION = "audience-mirror.blind-study/v0.1"
PARTICIPANT_PACK_SCHEMA_VERSION = "audience-mirror.blind-participant-pack/v0.1"
RESEARCHER_KEY_SCHEMA_VERSION = "audience-mirror.blind-researcher-key/v0.1"


def _variant_record(timeline: dict[str, Any], opaque_label: str) -> dict[str, Any]:
    asset = timeline["asset"]
    return {
        "opaque_label": opaque_label,
        "asset_id": asset["asset_id"],
        "variant_id": asset["variant_id"],
        "content_hash": asset["content_hash"],
        "timeline_id": timeline["timeline_id"],
        "timeline_hash": timeline_hash(timeline),
        "duration_ms": timeline["duration_ms"],
    }


def prepare_blind_study(
    timeline_a: dict[str, Any],
    timeline_b: dict[str, Any] | None = None,
    *,
    participant_slots: int = 12,
    seed: int = 20260821,
    experiment_id: str | None = None,
) -> dict[str, dict[str, Any]]:
    """Build a deterministic single-variant or counterbalanced A/B packet."""

    validate_timeline(timeline_a)
    if timeline_b is not None:
        validate_timeline(timeline_b)
    if participant_slots < 2:
        raise ValueError("participant_slots must be at least 2 for an exploratory blind study")
    if timeline_b is not None:
        asset_a = timeline_a["asset"]
        asset_b = timeline_b["asset"]
        if asset_a["asset_id"] != asset_b["asset_id"]:
            raise ValueError("A/B timelines must refer to the same conceptual asset_id")
        if asset_a["content_hash"] == asset_b["content_hash"]:
            raise ValueError("A/B timelines must have different content hashes")

    variants = [_variant_record(timeline_a, "cut-x")]
    if timeline_b is not None:
        variants.append(_variant_record(timeline_b, "cut-y"))
    study_material = {
        "variant_fingerprints": [item["timeline_hash"] for item in variants],
        "participant_slots": participant_slots,
        "seed": seed,
    }
    study_id = f"study-{fingerprint(study_material)[:12]}"
    experiment_id = experiment_id or f"exp-{study_id.removeprefix('study-')}"
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    cells = ["ab" if index % 2 == 0 else "ba" for index in range(participant_slots)]
    if timeline_b is None:
        cells = ["a_only"] * participant_slots
    random.Random(seed).shuffle(cells)
    assignments = []
    participant_rows = []
    for index, cell in enumerate(cells, start=1):
        slot_id = f"slot-{index:03d}"
        order = ["cut-x"] if cell == "a_only" else (["cut-x", "cut-y"] if cell == "ab" else ["cut-y", "cut-x"])
        assignments.append(
            {
                "participant_slot_id": slot_id,
                "counterbalance_cell": cell,
                "exposure_order": order,
            }
        )
        participant_rows.append(
            {
                "participant_slot_id": slot_id,
                "counterbalance_cell": cell,
                "exposure_order": order,
            }
        )

    plan = {
        "schema_version": BLIND_STUDY_SCHEMA_VERSION,
        "study_id": study_id,
        "experiment_id": experiment_id,
        "generated_at": generated_at,
        "purpose": "exploratory_human_convergence",
        "design": {
            "reception_context": "independent_blind",
            "outcome_blinded": True,
            "condition_mapping_blinded_to_participants": True,
            "participant_slots": participant_slots,
            "variant_count": len(variants),
            "counterbalanced": timeline_b is not None,
            "randomization_seed": seed,
            "statistical_representativeness_claimed": False,
            "calibration_level_target": "u1_exploratory_only",
        },
        "variants": variants,
        "measures": [
            {"instrument_type": "timestamp_issue", "metric_ids": ["confusion", "dropoff", "friction", "purchase_objection"]},
            {"instrument_type": "post_view_scale", "metric_ids": ["comprehension", "attention_proxy", "continue_intent", "share_intent", "consider_paying"]},
            {"instrument_type": "interview_code", "metric_ids": ["top_issue", "memorable_moment", "missing_context"]},
            *([{"instrument_type": "ab_choice", "metric_ids": ["direction", "reason"]}] if timeline_b is not None else []),
        ],
        "pre_registered_metrics": [
            *(["ab_direction_agreement"] if timeline_b is not None else []),
            "top_issue_recall_at_k",
            "timestamp_issue_recall",
            "repeat_run_stability",
            "completion_time",
        ],
        "governance": {
            "participant_identity_collected_in_packet": False,
            "consent_record_required_before_exposure": True,
            "human_anchor_schema": "audience-mirror.human-anchor/v0.1",
            "withdrawal_invalidates_analysis": True,
            "researcher_key_must_be_access_separated": True,
        },
        "limitations": [
            "Participant slots are planned assignments, not recruited or completed human participants.",
            "An 8–12 person study is exploratory and cannot establish population representativeness.",
            "Agent outputs must be frozen before Human Anchors are unblinded or imported.",
            "Calibration and held-out acceptance participants must remain separate in later C1 work.",
        ],
    }
    participant_pack = {
        "schema_version": PARTICIPANT_PACK_SCHEMA_VERSION,
        "study_id": study_id,
        "experiment_id": experiment_id,
        "outcome_blinded": True,
        "participant_identity_fields": [],
        "instructions": [
            "Do not disclose market outcomes, public comments, creator identity or condition mapping before response lock.",
            "Record timestamped issues during exposure and post-view measures only after the assigned cut ends.",
            "Store consent and identity outside this packet; use only the assigned slot ID in exported observations.",
        ],
        "assignments": participant_rows,
    }
    researcher_key = {
        "schema_version": RESEARCHER_KEY_SCHEMA_VERSION,
        "study_id": study_id,
        "experiment_id": experiment_id,
        "data_classification": "internal",
        "export_policy": "no_export",
        "access_separation_required": True,
        "variants": variants,
        "assignments": assignments,
        "unblind_after": "agent_outputs_frozen_and_human_responses_locked",
    }
    return {
        "study_plan": plan,
        "participant_pack": participant_pack,
        "researcher_key": researcher_key,
    }
