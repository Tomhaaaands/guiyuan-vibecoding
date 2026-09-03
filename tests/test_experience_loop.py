"""Tests for P6 experience loop and shadow red-line evaluation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from artifact_store import ArtifactStore
from experience_loop import (
    collect_experience,
    shadow_evaluate,
    write_draft_red_lines,
    write_experience,
)
from receipt_loop import record_receipt


class ExperienceLoopTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = ArtifactStore(self.root)
        self.store.init()
        self.store.write(
            "tasks/auth-01",
            "tasks",
            "## id\ntasks/auth-01\n## title\nauth\n## acceptance\nlogin works\n"
            "## status\nproposed\n## priority\n1\n",
            status="accepted",
        )

    def _failing_receipt(self, verdict="fail", error="integration test failed"):
        return record_receipt(
            self.store,
            "tasks/auth-01",
            verdict=verdict,
            checks=[{"name": "tests", "ok": False}],
            error=error,
        )

    def test_ignores_pass_receipts(self):
        record_receipt(self.store, "tasks/auth-01", verdict="pass", checks=[{"name": "t", "ok": True}])
        self.assertEqual(collect_experience(self.store), [])

    def test_collects_failed_receipt(self):
        self._failing_receipt()
        cands = collect_experience(self.store)
        self.assertEqual(len(cands), 1)
        self.assertIn("task", cands[0])
        self.assertEqual(cands[0]["slug"], "auth-01")

    def test_shadow_evaluate_min_frequency(self):
        self._failing_receipt()
        self.assertEqual(len(shadow_evaluate(self.store, min_frequency=1)), 1)
        self.assertEqual(len(shadow_evaluate(self.store, min_frequency=2)), 0)

    def test_write_experience_draft(self):
        self._failing_receipt()
        cands = collect_experience(self.store)
        target = write_experience(self.store, cands[0]["slug"], cands[0])
        artifact = self.store.get(target)
        self.assertEqual(artifact.metadata.kind, "experience")
        self.assertEqual(artifact.metadata.status, "draft")
        self.assertIn("[AI-DRAFT]", artifact.content)

    def test_write_draft_red_lines(self):
        self._failing_receipt()
        cands = collect_experience(self.store)
        path = write_draft_red_lines(self.root, cands)
        self.assertTrue(path.is_file())
        self.assertIn("[", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
