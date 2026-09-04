"""Tests for the manifest-independent human registry and confirmation anchors."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.anchor import record
from tools.project_registry import scan, write_registry


class RegistryAnchorTest(unittest.TestCase):
    def test_registry_maps_modules_and_machine_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs/01-product/chat").mkdir(parents=True)
            (root / "docs/02-technical/chat").mkdir(parents=True)
            (root / "docs/01-product/chat/prd.md").write_text("# Chat\n", encoding="utf-8")
            (root / "docs/01-product/chat/acceptance.md").write_text("# Accept\n", encoding="utf-8")
            (root / "docs/02-technical/chat/technical-spec.md").write_text("# Tech\n", encoding="utf-8")
            (root / "NOW.md").write_text("# now\n", encoding="utf-8")
            (root / "CHANGELOG.md").write_text("# log\n", encoding="utf-8")
            result = write_registry(root)
            self.assertEqual(result["modules"], 1)
            self.assertFalse(result["issues"])
            anchor_dir = root / ".guiyuan-vibecoding/anchors"
            anchor_dir.mkdir(parents=True)
            (anchor_dir / "R1-REQ.json").write_text("{}\n", encoding="utf-8")
            records, _, _ = scan(root)
            self.assertTrue(any(row["kind"] == "confirmation-anchor" for row in records))

    def test_anchor_is_immutable_and_hashes_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "REQ.md"
            source.write_text("connect agent", encoding="utf-8")
            path = record(root, "R66-REQ", "REQ", "accepted", ["REQ.md"], [], "PLANNING")
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(payload["input_hashes"]["REQ.md"].startswith("sha256:"))
            with self.assertRaises(FileExistsError):
                record(root, "R66-REQ", "REQ", "rejected", ["REQ.md"], [], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
