"""Tests for cross-artifact consistency checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from artifact_consistency import check
from tests.helpers import seeded_store


class ArtifactConsistencyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = seeded_store(Path(self.tmp.name))

    def test_clean_graph(self):
        self.assertEqual(check(self.store), [])

    def test_accepted_product_spec_without_acceptance(self):
        self.store.write(
            "product/noaccept",
            "product-spec",
            "## scope\nno acceptance clause here\n",
            status="accepted",
        )
        issues = check(self.store)
        self.assertTrue(any(i["rule"] == "missing_acceptance" for i in issues))

    def test_state_claim_without_receipts(self):
        self.store.write(
            "project-state",
            "project-state",
            "## stage\nDELIVERY\n## task\ntasks/auth-01\n",
            status="accepted",
        )
        issues = check(self.store)
        self.assertTrue(any(i["rule"] == "state_without_receipt" for i in issues))

    def test_supersedes_gap(self):
        # head is @2; ask to supersede @99.
        self.store.write("product/arc", "product-spec", "## acceptance\nv1\n", status="accepted")
        self.store.write(
            "product/arc",
            "product-spec",
            "## acceptance\nv2\n",
            status="accepted",
            supersedes="product/arc@199",
        )
        issues = check(self.store)
        self.assertTrue(any(i["rule"] == "supersedes_revision_gap" for i in issues))

    def test_accepted_superseded_is_warn(self):
        self.store.write("product/arc", "product-spec", "## acceptance\nv1\n", status="accepted")
        self.store.write(
            "product/arc",
            "product-spec",
            "## acceptance\nv2\n",
            status="review",
            supersedes="product/arc@1",
        )
        issues = check(self.store)
        self.assertTrue(any(i["rule"] == "accepted_superseded" and i["severity"] == "warn" for i in issues))


if __name__ == "__main__":
    unittest.main()
