"""Project-state detection regressions for Markdown-managed projects."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "skills" / "guiyuan-vibecoding" / "scripts" / "bootstrap.py"
SPEC = importlib.util.spec_from_file_location("guiyuan_bootstrap", BOOTSTRAP)
assert SPEC and SPEC.loader
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


class BootstrapDetectionTest(unittest.TestCase):
    def test_markdown_managed_without_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "04-workflow").mkdir(parents=True)
            for name in ("AGENTS.md", "NOW.md", "CHANGELOG.md"):
                (root / name).write_text("managed", encoding="utf-8")
            detected = bootstrap.detect_project_type(root)
            self.assertEqual(detected["type"], "md-managed")
            self.assertEqual(detected["runtime"], "none")


if __name__ == "__main__":
    unittest.main()
