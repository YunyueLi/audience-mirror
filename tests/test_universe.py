from __future__ import annotations

import unittest

from audience_mirror.universe import SEGMENTS, SyntheticPersonaUniverse


class SyntheticUniverseTests(unittest.TestCase):
    def test_generation_is_deterministic_and_balanced_by_construction(self) -> None:
        first = SyntheticPersonaUniverse(30, 42)
        second = SyntheticPersonaUniverse(30, 42)
        personas = first.cohort(30)
        self.assertEqual([item.to_dict() for item in personas], [item.to_dict() for item in second.cohort(30)])
        self.assertEqual(first.segment_counts(personas), {segment: 10 for segment in SEGMENTS})
        self.assertTrue(all(item.source == "synthetic_fixture" for item in personas))
        self.assertTrue(all(item.uncertainty["population_correspondence"] == "not_calibrated" for item in personas))
