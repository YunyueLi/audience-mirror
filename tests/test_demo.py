from __future__ import annotations

import json
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

from audience_mirror.adapters.matraix import AUDITED_COMMIT, MatrAixAdapter
from audience_mirror.demo import run_public_demo
from audience_mirror.domain import RunConfig


ROOT = Path(__file__).resolve().parents[1]
TIMELINE_PATH = ROOT / "fixtures" / "public-demo" / "timeline.json"


class _ReportLinkAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.fragments: list[str] = []
        self.trace_targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        href = values.get("href") or ""
        if href.startswith("#"):
            self.fragments.append(href[1:])
        if values.get("data-trace-target"):
            self.trace_targets.append(values["data-trace-target"] or "")


class PublicDemoTests(unittest.TestCase):
    def test_end_to_end_demo_outputs_evidence_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            summary = run_public_demo(
                timeline_path=TIMELINE_PATH,
                output_directory=directory,
                config=RunConfig(pool_size=120, deep_count=6, sweep_count=12, projection_count=120),
            )
            output = Path(directory)
            manifest = json.loads((output / "run-manifest.json").read_text(encoding="utf-8"))
            report = (output / "report.html").read_text(encoding="utf-8")
            self.assertTrue(summary["ok"])
            self.assertEqual(manifest["counts"]["deep_personas"], 6)
            self.assertEqual(manifest["counts"]["broad_sweep_runs"], 12)
            self.assertEqual(manifest["counts"]["projected_records"], 120)
            self.assertEqual(manifest["cost"]["model_calls"], 0)
            self.assertEqual(manifest["reception_context"]["condition"], "independent_blind")
            self.assertTrue(manifest["reception_context"]["outcome_blinded"])
            self.assertIn("六种数量，六种证据含义", report)
            self.assertIn("不证明虚拟用户能预测真人", report)
            self.assertIn("接受语境", report)
            self.assertIn("没有符合当前筛选条件的 Session。", report)
            self.assertNotIn("<script>alert", report)

            link_audit = _ReportLinkAudit()
            link_audit.feed(report)
            self.assertTrue(link_audit.trace_targets)
            self.assertFalse(set(link_audit.fragments) - link_audit.ids)
            self.assertFalse(set(link_audit.trace_targets) - link_audit.ids)
            self.assertTrue(all(target.startswith("trace-") for target in link_audit.trace_targets))
            for artifact in (
                "timeline.json",
                "deep-personas.json",
                "deep-traces.json",
                "broad-sweep.json",
                "population-projection.json",
                "matraix-media-contract.json",
                "run-manifest.json",
                "report.html",
            ):
                self.assertTrue((output / artifact).is_file(), artifact)

    def test_matraix_doctor_is_safe_without_checkout(self) -> None:
        report = MatrAixAdapter().doctor()
        self.assertFalse(report.available)
        self.assertEqual(report.audited_commit, AUDITED_COMMIT)
        self.assertFalse(report.persona_1m_bundled)
