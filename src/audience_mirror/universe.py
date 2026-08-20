"""Deterministic synthetic Persona Universe for public fixtures and tests."""

from __future__ import annotations

import random
from collections import Counter
from typing import Iterable

from .domain import Persona


SEGMENTS = (
    "genre_familiar",
    "general_streaming",
    "low_prior_short_form",
)

ATTENTION_CONTEXTS = (
    "focused_large_screen",
    "shared_living_room",
    "mobile_with_interruptions",
)


class SyntheticPersonaUniverse:
    """Generate non-identifiable personas from a stable seed.

    The universe is an engineering fixture. It is not calibrated to any real
    population and must never be labeled as a probability sample.
    """

    def __init__(self, size: int, seed: int) -> None:
        if size <= 0:
            raise ValueError("size must be positive")
        self.size = size
        self.seed = seed

    def persona_at(self, index: int) -> Persona:
        if index < 0 or index >= self.size:
            raise IndexError(index)
        segment_index = index % len(SEGMENTS)
        segment = SEGMENTS[segment_index]
        rng = random.Random((self.seed * 1_000_003) + index)

        if segment == "genre_familiar":
            familiarity = rng.uniform(0.72, 0.98)
            narrative_patience = rng.uniform(0.62, 0.95)
            novelty_preference = rng.uniform(0.48, 0.9)
            attention_context = ATTENTION_CONTEXTS[0]
        elif segment == "general_streaming":
            familiarity = rng.uniform(0.28, 0.66)
            narrative_patience = rng.uniform(0.42, 0.78)
            novelty_preference = rng.uniform(0.35, 0.72)
            attention_context = ATTENTION_CONTEXTS[1]
        else:
            familiarity = rng.uniform(0.02, 0.3)
            narrative_patience = rng.uniform(0.12, 0.48)
            novelty_preference = rng.uniform(0.55, 0.95)
            attention_context = ATTENTION_CONTEXTS[2]

        return Persona(
            persona_id=f"synthetic-persona-{index + 1:05d}",
            segment_id=segment,
            familiarity=round(familiarity, 4),
            narrative_patience=round(narrative_patience, 4),
            novelty_preference=round(novelty_preference, 4),
            price_sensitivity=round(rng.uniform(0.15, 0.9), 4),
            attention_context=attention_context,
            uncertainty={
                "population_correspondence": "not_calibrated",
                "behavioral_validity": "fixture_only",
            },
        )

    def cohort(self, count: int, *, offset: int = 0) -> list[Persona]:
        if count <= 0:
            raise ValueError("count must be positive")
        if offset < 0 or offset + count > self.size:
            raise ValueError("requested cohort is outside the universe")
        return [self.persona_at(index) for index in range(offset, offset + count)]

    def segment_counts(self, personas: Iterable[Persona]) -> dict[str, int]:
        counts = Counter(persona.segment_id for persona in personas)
        return {segment: counts.get(segment, 0) for segment in SEGMENTS}
