"""Tests for the P8 end-to-end MVP walkthrough."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mvp_walkthrough import run_walkthrough


class MvpWalkthroughTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_local_walkthrough_passes(self):
        report = run_walkthrough(self.root, "Add an admin dashboard.", provider="local-fallback")
        self.assertTrue(report["passed"])
        self.assertEqual(report["provider"], "local-fallback")
        self.assertIn("analysis_id", report)
        self.assertIsNotNone(report["receipt"])

    def test_walkthrough_ceiling_growth(self):
        report = run_walkthrough(self.root, "Add a tiny feature.", provider="local-fallback")
        self.assertTrue(report["passed"])
        self.assertLessEqual(report["context_tokens"], report["ceiling"])


if __name__ == "__main__":
    unittest.main()
