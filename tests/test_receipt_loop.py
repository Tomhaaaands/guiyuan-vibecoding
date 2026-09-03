"""Tests for P5 receipt loop execution/verification."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from artifact_store import ArtifactStore
from receipt_loop import (
    apply_receipt,
    record_receipt,
    run_cycle,
    update_task_status,
)
from tests.helpers import seeded_store


class ReceiptLoopTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = seeded_store(self.root)

    def test_invalid_verdict(self):
        with self.assertRaises(ValueError):
            record_receipt(self.store, "tasks/auth-01", verdict="bogus", checks=[])

    def test_record_receipt_revisioned(self):
        r1 = record_receipt(self.store, "tasks/auth-01", verdict="pass", checks=[{"name": "t", "ok": True}])
        r2 = record_receipt(self.store, "tasks/auth-01", verdict="pass", checks=[{"name": "t", "ok": True}])
        artifact1 = self.store.get(r1)
        artifact2 = self.store.get(r2)
        # Same task/checks -> same content -> idempotent store returns same metadata.
        self.assertEqual(artifact1.metadata.artifact_id, artifact2.metadata.artifact_id)

    def test_apply_receipt_pass_sets_done_and_delivery(self):
        applied = apply_receipt(self.store, "tasks/auth-01", "pass", None)
        self.assertEqual(applied["task_status"], "done")
        self.assertEqual(applied["stage"], "DELIVERY")

    def test_apply_receipt_fail_keeps_in_progress(self):
        applied = apply_receipt(self.store, "tasks/auth-01", "fail", "lint error")
        self.assertEqual(applied["task_status"], "in_progress")
        self.assertEqual(applied["stage"], "EXECUTION")

    def test_apply_receipt_blocked(self):
        applied = apply_receipt(self.store, "tasks/auth-01", "blocked", "tests fail")
        self.assertEqual(applied["task_status"], "blocked")
        self.assertEqual(applied["stage"], "EXECUTION")

    def test_update_task_status_appends_when_missing(self):
        self.store.write(
            "tasks/plain",
            "tasks",
            "## id\ntasks/plain\n## title\np\n## acceptance\np works\n",
            status="draft",
        )
        update_task_status(self.store, "tasks/plain", "done")
        self.assertIn("## status\ndone", self.store.get("tasks/plain").content)

    def test_run_cycle_unknown_task_raises(self):
        with self.assertRaises(ValueError):
            run_cycle(self.root, "tasks/missing", checks=[{"name": "t", "ok": True}])

    def test_run_cycle_pass(self):
        out = run_cycle(self.root, "tasks/auth-01", checks=[{"name": "tests", "ok": True}])
        self.assertEqual(out["verdict"], "pass")
        self.assertEqual(out["task_status"], "done")
        self.assertEqual(out["stage"], "DELIVERY")

    def test_run_cycle_all_ok_ignores_error(self):
        # Even with error text present, all checks ok -> pass.
        out = run_cycle(self.root, "tasks/auth-01", checks=[{"name": "t", "ok": True}], error="stale")
        self.assertEqual(out["verdict"], "pass")


if __name__ == "__main__":
    unittest.main()
