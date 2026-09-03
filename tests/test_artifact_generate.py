"""Tests for analysis -> authority-artifact generation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from artifact_generate import generate
from artifact_store import ArtifactStore


class ArtifactGenerateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def _seed_analysis(self):
        store = ArtifactStore(self.root)
        store.init()
        store.write(
            "analysis/build-login",
            "analysis",
            "# Analysis\n\n## intent\nBuild an email login\n\n"
            "## known_facts\n- **f1** users need email login (intent, 0.5)\n\n"
            "## decisions\n- **d1** use local provider (constraint, 0.8)\n\n"
            "## open_questions\n- **q1** confirm scope (heuristic, 1.0)\n\n",
            status="accepted",
        )
        return store

    def test_generate_writes_drafts(self):
        self._seed_analysis()
        out = generate(self.root, "analysis/build-login")
        self.assertEqual(out["status"], "draft")
        store = ArtifactStore(self.root)
        product = store.get(out["product_id"].split("@")[0])
        decisions = store.get(out["decisions_id"].split("@")[0])
        self.assertEqual(product.metadata.kind, "product-spec")
        self.assertEqual(decisions.metadata.kind, "decisions")
        self.assertIn("acceptance", product.content)
        self.assertIn("## constraint", decisions.content)

    def test_generate_keeps_status(self):
        self._seed_analysis()
        out = generate(self.root, "analysis/build-login", status="review")
        self.assertEqual(out["status"], "review")

    def test_generate_missing_analysis_raises(self):
        with self.assertRaises(KeyError):
            generate(self.root, "analysis/nope")


if __name__ == "__main__":
    unittest.main()
