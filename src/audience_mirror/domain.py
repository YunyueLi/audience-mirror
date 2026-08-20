"""Small, dependency-free domain types for the local experiment baseline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .hashing import fingerprint


@dataclass(frozen=True, slots=True)
class Persona:
    persona_id: str
    segment_id: str
    familiarity: float
    narrative_patience: float
    novelty_preference: float
    price_sensitivity: float
    attention_context: str
    source: str = "synthetic_fixture"
    uncertainty: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.persona_id:
            raise ValueError("persona_id must not be empty")
        if not self.segment_id:
            raise ValueError("segment_id must not be empty")
        for field_name in (
            "familiarity",
            "narrative_patience",
            "novelty_preference",
            "price_sensitivity",
        ):
            value = getattr(self, field_name)
            if not 0 <= value <= 1:
                raise ValueError(f"{field_name} must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "segment_id": self.segment_id,
            "familiarity": self.familiarity,
            "narrative_patience": self.narrative_patience,
            "novelty_preference": self.novelty_preference,
            "price_sensitivity": self.price_sensitivity,
            "attention_context": self.attention_context,
            "source": self.source,
            "uncertainty": self.uncertainty,
        }

    @property
    def snapshot_hash(self) -> str:
        return fingerprint(self.to_dict())


@dataclass(frozen=True, slots=True)
class RunConfig:
    experiment_id: str = "exp-public-fixture-v1"
    run_id: str = "run-public-fixture-v1"
    seed: int = 20260819
    pool_size: int = 10_000
    deep_count: int = 12
    sweep_count: int = 100
    projection_count: int = 10_000

    def __post_init__(self) -> None:
        if not self.experiment_id or not self.run_id:
            raise ValueError("experiment_id and run_id must not be empty")
        for field_name in ("pool_size", "deep_count", "sweep_count", "projection_count"):
            if getattr(self, field_name) <= 0:
                raise ValueError(f"{field_name} must be positive")
        if self.deep_count + self.sweep_count > self.pool_size:
            raise ValueError("deep and sweep cohorts together cannot exceed the persona pool")
        if self.projection_count > self.pool_size:
            raise ValueError("projection_count cannot exceed pool_size in the local baseline")

    def to_dict(self) -> dict[str, int | str]:
        return {
            "experiment_id": self.experiment_id,
            "run_id": self.run_id,
            "seed": self.seed,
            "pool_size": self.pool_size,
            "deep_count": self.deep_count,
            "sweep_count": self.sweep_count,
            "projection_count": self.projection_count,
        }
