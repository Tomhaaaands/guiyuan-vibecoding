"""Tests for the round archive helper (isolated temp paths)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import rollup_round


class RollupRoundTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.arch = self.root / "docs" / "04-workflow" / "archive"
        self.cl = self.root / "docs" / "04-workflow" / "changelog.md"
        self.arch.mkdir(parents=True)
        self.cl.write_text(
            "# Changelog\n\n| Round | Date | Module | Conclusion | Archive |\n| --- | --- | --- | --- | --- |\n",
            encoding="utf-8",
        )

    def _run(self, argv):
        with mock.patch.object(rollup_round, "ARCH", self.arch), \
             mock.patch.object(rollup_round, "CL", self.cl), \
             mock.patch.object(rollup_round, "ROOT", self.root), \
             mock.patch("sys.argv", ["rollup_round.py", *argv]):
            rollup_round.main()

    def test_write_archive_and_changelog_row(self):
        detail = self.root / "detail.md"
        detail.write_text("details here", encoding="utf-8")
        self._run(["--round", "R48", "--date", "2026-09-03", "--module", "qa",
                   "--summary", "test suite added", "--detail", str(detail)])
        self.assertTrue((self.arch / "2026-09-03-r48.md").is_file())
        self.assertIn("| R48 |", self.cl.read_text(encoding="utf-8"))

    def test_rerun_does_not_crash(self):
        detail = self.root / "detail.md"
        detail.write_text("details here", encoding="utf-8")
        self._run(["--round", "R48", "--date", "2026-09-03", "--module", "qa",
                   "--summary", "test suite added", "--detail", str(detail)])
        # Re-running the same round must not crash and must keep the archive file present.
        self._run(["--round", "R48", "--date", "2026-09-03", "--module", "qa",
                   "--summary", "test suite added", "--detail", str(detail)])
        self.assertTrue((self.arch / "2026-09-03-r48.md").is_file())


if __name__ == "__main__":
    unittest.main()
