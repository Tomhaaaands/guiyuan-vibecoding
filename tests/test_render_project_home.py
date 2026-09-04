"""Regression tests for the static project-home renderer."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("render_project_home", ROOT / "tools" / "render_project_home.py")
assert SPEC and SPEC.loader
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


class RenderProjectHomeTest(unittest.TestCase):
    def test_renders_template_with_project_facts_and_no_server_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "templates").mkdir()
            (root / "templates" / "guiyuan-vibecoding-home.html").write_text(
                (ROOT / "guiyuan-vibecoding-home.html").read_text(encoding="utf-8"), encoding="utf-8"
            )
            (root / "README.md").write_text("# Demo Project\n\nA local demo.\n", encoding="utf-8")
            (root / "VERSION").write_text("1.2.3\n", encoding="utf-8")
            (root / "NOW.md").write_text("# NOW (2026-09-04)\n\nNext.\n", encoding="utf-8")
            (root / "CHANGELOG.md").write_text(
                "| Round | Date | Module | Conclusion | Archive |\n| --- | --- | --- | --- | --- |\n"
                "| R1 | 09-04 | demo | initial | [r1](archive/2026-09-04-r1.md) |\n", encoding="utf-8"
            )
            out = root / "status.html"
            renderer.render(root, out, "local", 10)
            page = out.read_text(encoding="utf-8")
            self.assertIn('"title": "Demo Project"', page)
            self.assertIn('"version": "1.2.3"', page)
            self.assertIn("var PROJECT =", page)
            self.assertNotIn("8010", page)
            self.assertNotIn("serve_project", page)

    def test_inlines_assets_from_template_adjacent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "templates" / "assets").mkdir(parents=True)
            (root / "templates" / "guiyuan-vibecoding-home.html").write_text(
                '<style>.hero{background:url("assets/taoyuanming-2.png")}</style>\n'
                'var PROJECT = {};\n\n(function(){}',
                encoding="utf-8",
            )
            (root / "templates" / "assets" / "taoyuanming-2.png").write_bytes(b"fake-png")
            (root / "README.md").write_text("# Demo Project\n", encoding="utf-8")
            out = root / "status.html"
            renderer.render(root, out, "local", 10)
            page = out.read_text(encoding="utf-8")
            self.assertIn("url(\"data:image/png;base64,ZmFrZS1wbmc=\")", page)
            self.assertNotIn('url("assets/taoyuanming-2.png")', page)


if __name__ == "__main__":
    unittest.main()
