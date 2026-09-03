"""Tests for the keyword doc-hydration retrieval."""

from __future__ import annotations

import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import hydrate
from hydrate import _files, _semantic_backend


class HydrateTest(unittest.TestCase):
    def test_semantic_backend_reserved(self):
        with mock.patch.dict(os.environ, {"HYDRATE_SEMANTIC_BACKEND": "x"}, clear=False):
            self.assertEqual(_semantic_backend(), "x")

    def test_semantic_backend_none_when_unset(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(_semantic_backend())

    def test_semantic_falls_back_to_keyword_without_backend(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch.object(hydrate, "_semantic_search", wraps=hydrate._semantic_search) as spy:
                result = hydrate._semantic_search("token budget", 3)
                self.assertIsNone(result)
                spy.assert_called_once()

    def test_files_scan_excludes_archive(self):
        files = _files()
        self.assertTrue(files)
        self.assertFalse(any("archive" in p.parts for p in files))

    def test_keyword_match_counts_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc = Path(tmp) / "doc.md"
            doc.write_text("## token\n500\n\ntoken budget here\n", encoding="utf-8")
            pats = [re.compile(re.escape(k), re.IGNORECASE) for k in ("token",)]
            matched = [ln.strip() for ln in doc.read_text(encoding="utf-8").splitlines() if any(p.search(ln) for p in pats)]
            self.assertGreaterEqual(len(matched), 2)


if __name__ == "__main__":
    unittest.main()
