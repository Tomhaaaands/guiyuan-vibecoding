"""Tests for the pitfalls distillation pipeline."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from distill import _candidates, _dedupe, _scan_files, run_pitfalls


class DistillTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        archive = self.root / "docs" / "04-workflow" / "archive"
        archive.mkdir(parents=True)
        (archive / "r1.md").write_text(
            "# R1\n\n这是踩坑记录：不许暴露密钥。\n", encoding="utf-8"
        )

    def test_scan_finds_archive(self):
        files = _scan_files(self.root)
        self.assertEqual(len(files), 1)

    def test_candidates_match_pitfall_marker(self):
        files = _scan_files(self.root)
        cands = _candidates(files)
        self.assertEqual(len(cands), 1)

    def test_dedupe_limit(self):
        cands = [
            (Path("a"), 1, "红线", "same line"),
            (Path("b"), 1, "红线", "same line"),
            (Path("c"), 1, "红线", "different line"),
        ]
        out = _dedupe(cands, 2)
        self.assertEqual(len(out), 2)

    def test_run_no_archive_prints_nothing_to_distill(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            run_pitfalls(Path(empty_dir), limit=5, apply=False)


if __name__ == "__main__":
    unittest.main()
